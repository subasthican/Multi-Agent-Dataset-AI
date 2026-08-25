import os
from functools import lru_cache
from typing import Dict, List

import spacy

DEFAULT_MODEL_NAME = "en_core_web_sm"


@lru_cache(maxsize=1)
def get_nlp_model():
    model_name = os.getenv("NLP_SPACY_MODEL", DEFAULT_MODEL_NAME)
    return spacy.load(model_name)


def clean_text(text: str) -> str:
    return " ".join(text.strip().split())


def extract_keywords(doc) -> List[str]:
    keywords: List[str] = []
    for token in doc:
        if token.is_stop or token.is_punct or token.is_space:
            continue
        if token.pos_ in ("NOUN", "PROPN"):
            lemma = token.lemma_.lower()
            if lemma not in keywords:
                keywords.append(lemma)
    return keywords


def extract_entities(doc) -> List[Dict[str, str]]:
    return [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
