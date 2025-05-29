from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.models.user import User
from app.models.revoked_token import RevokedToken
from app.schemas.user import UserCreate, Token
from app.core.security import get_password_hash, verify_password, create_access_token, decode_token
from app.db.session import SessionLocal
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from datetime import timedelta, datetime

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")

        if db.query(RevokedToken).filter(RevokedToken.jti == jti).first():
            raise HTTPException(
                status_code=401, detail="Token has been revoked")

        user_email: str = payload.get("sub")
        if user_email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == user_email).first()
    if user is None:
        raise credentials_exception
    return user


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


@router.post("/register", response_model=Token)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="email already taken")

    user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": token, "email": user.email, "token_type": "bearer"}


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    token = request.headers.get("Authorization").split()[1]
    payload = jwt.decode(token, SECRET_KEY,
                         algorithms=[ALGORITHM])
    jti = payload.get("jti")

    if jti:
        revoked = RevokedToken(
            jti=jti, expires_at=datetime.fromtimestamp(payload["exp"]))
        db.add(revoked)
        db.commit()
        return {"msg": "Successfully logged out"}
    else:
        raise HTTPException(status_code=400, detail="Invalid token")


@router.get("/me")
def read_users_me(token: str = Depends(oauth2_scheme)):
    token_data = decode_token(token)
    if not token_data or not token_data.email:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {
        "email": token_data.email
    }


@router.get("/user")
def get_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = get_current_user(token, db)
    return {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name
    }
