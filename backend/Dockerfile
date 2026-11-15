# Multi-stage Python runtime for Smart Quiz API
FROM python:3.12-slim AS runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application source code and migrations
COPY . .

# Expose default port
EXPOSE 8000

# Run database migration check and start uvicorn
CMD ["sh", "-c", "alembic upgrade head && python scripts/seed.py --with-demo-exam && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
