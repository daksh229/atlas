"""
rag.py — retrieval layer for the knowledge route.

Embeds the unstructured corpus (data/corpus.json) and does region-filtered
top-k similarity search. Pluggable embedder:

  - sentence-transformers (local, dense) — set RAG_EMBEDDER=st (default if installed)
  - TF-IDF (scikit-learn) fallback — always works offline, no model download
  - (production) swap in Voyage AI embeddings behind the same Embedder interface

RBAC: retrieval is region-scoped exactly like SQL. A trader's query only ever
matches documents in their region (plus region-agnostic brand docs); a manager
(region None / "All regions") sees everything.
"""

import json
import os
from functools import lru_cache

import numpy as np

from app.core.config import settings

CORPUS_PATH = os.path.join(settings.DATA_DIR, "corpus.json")
EMBEDDER = os.getenv("RAG_EMBEDDER", "auto")  # auto | st | tfidf


# --------------------------------------------------------------- embedders ----

class TfidfEmbedder:
    name = "tfidf (offline fallback)"

    def __init__(self, texts: list[str]):
        from sklearn.feature_extraction.text import TfidfVectorizer

        self._vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
        self._matrix = self._vec.fit_transform(texts)  # sparse [n, vocab]

    def encode_docs(self) -> np.ndarray:
        return self._matrix

    def encode_query(self, query: str):
        return self._vec.transform([query])

    def similarity(self, q, docs) -> np.ndarray:
        from sklearn.metrics.pairwise import linear_kernel  # cosine on L2-normed tf-idf

        return linear_kernel(q, docs).ravel()


class STEmbedder:
    name = "sentence-transformers (local dense)"

    def __init__(self, texts: list[str], model="all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model)
        self._docs = self._model.encode(texts, normalize_embeddings=True)

    def encode_docs(self) -> np.ndarray:
        return self._docs

    def encode_query(self, query: str) -> np.ndarray:
        return self._model.encode([query], normalize_embeddings=True)

    def similarity(self, q, docs) -> np.ndarray:
        return (docs @ q.T).ravel()  # cosine (vectors are normalized)


def _make_embedder(texts: list[str]):
    want = EMBEDDER
    if want in ("auto", "st"):
        try:
            return STEmbedder(texts)
        except Exception:
            if want == "st":
                # explicitly requested but unavailable → still degrade gracefully
                pass
    return TfidfEmbedder(texts)


# ------------------------------------------------------------------ index -----

class _Index:
    def __init__(self):
        with open(CORPUS_PATH, "r", encoding="utf-8") as f:
            self.docs = json.load(f)
        # Embed "title. text" so titles contribute to the match.
        texts = [f"{d['title']}. {d['text']}" for d in self.docs]
        self.embedder = _make_embedder(texts)
        self._doc_vecs = self.embedder.encode_docs()

    def search(self, query: str, region: str | None, k: int = 4) -> list[dict]:
        scores = self.embedder.similarity(self.embedder.encode_query(query), self._doc_vecs)
        ranked = np.argsort(scores)[::-1]
        out = []
        for i in ranked:
            d = self.docs[int(i)]
            # RBAC: region-agnostic docs (region=None) are visible to everyone;
            # otherwise the doc's region must match the caller's region.
            if region and region != "All regions" and d["region"] not in (None, region):
                continue
            out.append({**d, "score": round(float(scores[int(i)]), 3)})
            if len(out) >= k:
                break
        return out


@lru_cache(maxsize=1)
def _index() -> _Index:
    return _Index()


def engine_name() -> str:
    return _index().embedder.name


def retrieve(query: str, region: str | None = None, k: int = 4) -> list[dict]:
    return _index().search(query, region, k)
