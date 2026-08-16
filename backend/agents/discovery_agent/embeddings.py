import os
from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    model_name = os.getenv("DISCOVERY_EMBEDDING_MODEL", DEFAULT_MODEL_NAME)
    return SentenceTransformer(model_name)


def create_embeddings(texts: List[str]):
    return get_embedding_model().encode(texts)
