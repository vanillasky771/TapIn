# Dockerfile at repo root

FROM python:3.11-slim

# Install system deps (optional, but helpful for psycopg2 etc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Let Railway pass PORT, default to 8000 if not set
ENV PORT=8000

# Start FastAPI with uvicorn
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
