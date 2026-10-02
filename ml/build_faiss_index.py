"""Step 2: build a FAISS inner-product index over the (unit-length) destination embeddings.

    python ml/build_faiss_index.py

Inner product on unit vectors equals cosine similarity. IndexFlatIP is exact search, which is
the right choice for tens to thousands of destinations; switch to IndexIVFFlat or HNSW past ~100k.
"""

import json

import _common  # noqa: F401  (sets sys.path)
import faiss
import numpy as np

from app.ml.semantic import ARTIFACT_DIR


def main() -> None:
    vectors = np.load(ARTIFACT_DIR / "destination_embeddings.npy").astype("float32")
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    faiss.write_index(index, str(ARTIFACT_DIR / "destinations.faiss"))
    meta = json.loads((ARTIFACT_DIR / "meta.json").read_text())
    print(f"FAISS IndexFlatIP: {index.ntotal} vectors, dim {vectors.shape[1]}, embeddings from {meta['backend']}")

    # Sanity check: every destination's nearest neighbour is itself.
    _, nn = index.search(vectors, 1)
    assert (nn[:, 0] == np.arange(len(vectors))).all(), "index self-check failed"
    print("Self-check passed.")


if __name__ == "__main__":
    main()
