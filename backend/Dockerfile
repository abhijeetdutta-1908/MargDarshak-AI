# Build context is the repo root so database/ (migrations, seed) and ml/ ship with the backend.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    HF_HOME=/srv/models HF_HUB_DISABLE_TELEMETRY=1
WORKDIR /srv/backend

COPY backend/requirements.txt backend/requirements-ml.txt ./
RUN pip install --no-cache-dir torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt -r requirements-ml.txt

# Bake the embedding model into the image so the container never needs to download at runtime.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

COPY backend/ /srv/backend/
COPY database/ /srv/database/
COPY ml/ /srv/ml/

# Prebuild destination embeddings + FAISS index (the engine verifies their fingerprint at startup).
RUN python ../ml/create_embeddings.py && python ../ml/build_faiss_index.py

RUN useradd --create-home appuser && chown -R appuser /srv/models
USER appuser
ENV HF_HUB_OFFLINE=1

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && python ../database/seed.py && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
