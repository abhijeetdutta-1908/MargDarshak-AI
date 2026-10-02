"""Text embeddings + vector search.

Primary: Sentence Transformers (all-MiniLM-L6-v2) + FAISS inner-product index.
Fallbacks, chosen automatically and reported to the caller:
  - embeddings: TF-IDF (scikit-learn) when sentence-transformers or the model is unavailable
  - index: exact NumPy cosine search when faiss is not installed
"""

import hashlib
import json
import logging
import os
from functools import lru_cache
from pathlib import Path

import numpy as np

log = logging.getLogger("margdarshak.ml")

DEFAULT_MODEL = os.getenv("SENTENCE_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
ARTIFACT_DIR = Path(os.getenv("ML_ARTIFACTS_DIR", Path(__file__).resolve().parents[3] / "ml" / "artifacts"))


def destination_text(name: str, category: str, tags: list[str], description: str) -> str:
    return f"{name}. A {category} destination. Known for {', '.join(tags)}. {description}"


@lru_cache(maxsize=2)
def _load_transformer(model_name: str):
    if os.getenv("DISABLE_SENTENCE_TRANSFORMERS") == "1":
        return None
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(model_name, device="cpu")
    except Exception as exc:  # missing package, no network to download, corrupt cache...
        log.warning("Sentence Transformers unavailable (%s); falling back to TF-IDF", exc)
        return None


def _normalise(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype="float32")
    norms = np.linalg.norm(v, axis=1, keepdims=True)
    return v / np.where(norms == 0, 1, norms)


class Embedder:
    """Encodes text to unit vectors. Call fit() with the corpus first (needed by TF-IDF)."""

    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self._model = _load_transformer(model_name)
        self._tfidf = None

    @property
    def backend(self) -> str:
        return f"sentence-transformers/{self.model_name.split('/')[-1]}" if self._model else "tfidf"

    def fit(self, corpus: list[str]) -> "Embedder":
        if self._model is None:
            from sklearn.feature_extraction.text import TfidfVectorizer

            self._tfidf = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True).fit(corpus)
        return self

    def encode(self, texts: list[str]) -> np.ndarray:
        if self._model is not None:
            return _normalise(self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False))
        if self._tfidf is None:
            raise RuntimeError("TF-IDF embedder must be fit() before encode()")
        return _normalise(self._tfidf.transform(texts).toarray())


class VectorIndex:
    """Cosine-similarity search over unit vectors (FAISS IndexFlatIP, NumPy fallback)."""

    def __init__(self, vectors: np.ndarray, faiss_index=None):
        self.vectors = np.ascontiguousarray(vectors, dtype="float32")
        self._faiss = faiss_index
        if self._faiss is None:
            try:
                import faiss

                self._faiss = faiss.IndexFlatIP(self.vectors.shape[1])
                self._faiss.add(self.vectors)
            except ImportError:
                log.info("faiss not installed; using exact NumPy search")

    @property
    def backend(self) -> str:
        return "faiss" if self._faiss is not None else "numpy"

    def search(self, query: np.ndarray, k: int) -> list[tuple[int, float]]:
        q = np.ascontiguousarray(query.reshape(1, -1), dtype="float32")
        k = min(k, len(self.vectors))
        if self._faiss is not None:
            scores, idx = self._faiss.search(q, k)
            return [(int(i), float(s)) for i, s in zip(idx[0], scores[0], strict=True) if i >= 0]
        sims = self.vectors @ q[0]
        order = np.argsort(-sims)[:k]
        return [(int(i), float(sims[i])) for i in order]


def fingerprint(texts: list[str], backend: str) -> str:
    return hashlib.sha256((backend + "\n" + "\n".join(texts)).encode()).hexdigest()[:16]


def save_artifacts(ids: list[int], vectors: np.ndarray, backend: str, fp: str, directory: Path = ARTIFACT_DIR) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    np.save(directory / "destination_embeddings.npy", vectors)
    (directory / "meta.json").write_text(json.dumps({"ids": ids, "backend": backend, "fingerprint": fp}))


def load_artifacts(fp: str, directory: Path = ARTIFACT_DIR):
    """Return (vectors, faiss_index|None) if artifacts were built for exactly this corpus, else None."""
    try:
        meta = json.loads((directory / "meta.json").read_text())
        if meta["fingerprint"] != fp:
            return None
        vectors = np.load(directory / "destination_embeddings.npy")
        index = None
        if (directory / "destinations.faiss").exists():
            import faiss

            index = faiss.read_index(str(directory / "destinations.faiss"))
        return vectors, index
    except (OSError, KeyError, ValueError, ImportError):
        return None
