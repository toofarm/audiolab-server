from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router as api_router
from app.models import User, Track, Sample, Project, GeneratedAudio, RevokedToken  # Import all models to ensure relationships are set up

app = FastAPI(title="Audio Analyzer API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js development server
        "http://localhost:3001",  # Alternative Next.js port
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://127.0.0.1:3001",  # Alternative localhost port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
