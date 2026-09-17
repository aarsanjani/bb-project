# Use official Python lightweight runtime
FROM python:3.11-slim

# Set environment variables for non-buffered logging and Vertex AI
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    GOOGLE_GENAI_USE_VERTEXAI=true \
    GOOGLE_CLOUD_PROJECT=arsanjani-genai \
    GOOGLE_CLOUD_LOCATION=us-central1 \
    PYTHONPATH=/app

WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application source code
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# Expose server port
EXPOSE 8080

# Execute production Gunicorn server with worker class supporting SSE streaming
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "8", "--timeout", "0", "backend.app:app"]
