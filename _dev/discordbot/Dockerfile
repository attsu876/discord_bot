# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps for building some wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first for better caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . /app

# Default DB path inside container; override via env
ENV DATABASE_PATH=/app/data/lesson_logs.db \
    OUTPUT_DIR=/app/output

# Create folders for volume mounts
RUN mkdir -p /app/data /app/output

CMD ["python", "run.py"]
