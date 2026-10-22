FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

RUN python -m spacy download en_core_web_sm
RUN python -c "import nltk; nltk.download('wordnet'); nltk.download('punkt'); nltk.download('punkt_tab', quiet=True); nltk.download('averaged_perceptron_tagger'); nltk.download('omw-1.4')"

COPY backend/ /app/backend/
COPY models/ /app/models/
COPY proposed_asag/ /app/proposed_asag/
COPY base_asag/ /app/base_asag/
COPY baseline/ /app/baseline/
COPY common/ /app/common/
COPY data/ /app/data/
COPY evaluation/ /app/evaluation/

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "backend.main:app"]
