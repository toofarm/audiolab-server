FROM python:3.11-slim

WORKDIR /app

# Add ffmpeg install here
RUN apt-get update && apt-get install -y ffmpeg

COPY ./app /app/app
COPY ./requirements /app/requirements
COPY alembic.ini /app/
COPY alembic /app/alembic

RUN pip install --no-cache-dir -r requirements/dev.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
