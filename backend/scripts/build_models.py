"""Download/package inference assets during build, without opening the database."""
import json
import os
from pathlib import Path

import spacy
from sentence_transformers import SentenceTransformer

BACKEND = Path(__file__).resolve().parents[1]


def main():
    nlp_name = os.getenv("NLP_SPACY_MODEL", "en_core_web_sm")
    spacy.load(nlp_name)  # The compatible English wheel is in requirements.txt.
    model_name = os.getenv("DISCOVERY_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    destination = BACKEND / "model_assets/embeddings"
    model = SentenceTransformer(model_name, device="cpu")
    model.save(str(destination))
    # Verify the packaged model works without a remote model download.
    bundled = SentenceTransformer(str(destination), local_files_only=True, device="cpu")
    vectors = bundled.encode(["Medical records for diabetes classification"])
    assert vectors.shape[0] == 1 and vectors.shape[1] > 0
    print(json.dumps({"embedding_model": model_name, "spacy_model": nlp_name,
                      "bundled_model_bytes": sum(p.stat().st_size for p in destination.rglob("*") if p.is_file()),
                      "offline_load": "PASS"}))


if __name__ == "__main__":
    main()
