"""Step 1: encode every destination description into a vector.

    python ml/create_embeddings.py

Writes ml/artifacts/destination_embeddings.npy and meta.json (model + corpus fingerprint).
The backend reuses these only if the fingerprint matches its current catalogue; otherwise it
re-encodes at startup, so stale artifacts can never produce wrong results.
"""

from _common import destination_texts, destinations_frame

from app.ml.semantic import ARTIFACT_DIR, Embedder, fingerprint, save_artifacts


def main() -> None:
    df = destinations_frame()
    texts = destination_texts(df)
    embedder = Embedder().fit(texts)
    if embedder.backend == "tfidf":
        print("Sentence Transformers unavailable: artifacts would be TF-IDF vectors, which are rebuilt at startup anyway.")
    vectors = embedder.encode(texts)
    save_artifacts(df["name"].tolist(), vectors, embedder.backend, fingerprint(texts, embedder.backend))
    print(f"Encoded {len(texts)} destinations with {embedder.backend} -> {vectors.shape} in {ARTIFACT_DIR}")


if __name__ == "__main__":
    main()
