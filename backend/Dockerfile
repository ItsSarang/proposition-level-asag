# Production Dockerfile for ASAG Flask Backend Engine
FROM python:3.11-slim

LABEL maintainer="ASAG Research Team"
LABEL description="Proposition-Level ASAG Scoring & Analysis Backend"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Download required spaCy language model and NLTK data assets
RUN python -m spacy download en_core_web_sm
RUN python -c "import nltk; nltk.download('wordnet'); nltk.download('punkt'); nltk.download('punkt_tab', quiet=True); nltk.download('averaged_perceptron_tagger'); nltk.download('omw-1.4')"

# Copy backend service and core ASAG engine modules
COPY backend/ /app/backend/
COPY models/ /app/models/
COPY proposed_asag/ /app/proposed_asag/
COPY base_asag/ /app/base_asag/
COPY baseline/ /app/baseline/
COPY common/ /app/common/
COPY data/ /app/data/

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

EXPOSE 8000

# Health check to ensure API is responding
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Production WSGI server using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "backend.main:app"]
