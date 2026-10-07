"""Keep a specific subject from being replaced by a broad domain match."""
import re

TOPICS = {
    "cancer": ("cancer", "tumor", "tumour", "carcinoma", "oncology", "malignant", "malignancy"),
    "diabetes": ("diabetes", "diabetic"),
    "heart disease": ("heart disease", "cardiovascular", "cardiac"),
    "fraud": ("fraud", "fraudulent"),
    "stock": ("stock", "stocks", "equity", "equities"),
    "solar": ("solar", "photovoltaic"),
    "air quality": ("air quality", "air pollution"),
    "housing": ("house", "housing", "real estate", "property"),
    "churn": ("churn", "attrition"),
    "student": ("student", "students", "academic"),
    "course completion": ("course completion", "course dropout", "mooc"),
}


def contains(text, term):
    return re.search(rf"\b{re.escape(term)}\b", text.lower()) is not None


def requested_topics(query):
    return [topic for topic, aliases in TOPICS.items() if any(contains(query, alias) for alias in aliases)]


def matches_topic(dataset, requirement):
    text = f"{dataset.name} {dataset.description}"
    topics = requested_topics(requirement.original_query)
    if topics:
        return all(any(contains(text, alias) for alias in TOPICS[topic]) for topic in topics)
    generic = {"data", "dataset", "datasets", "prediction", "classification", "regression", "clustering",
               "image", "images", "text", "tabular", "time", "series", "machine", "learning", "task",
               "healthcare", "medical", "health", "patient", "patients", "record", "records", "finance",
               "financial", "business", "education", "environment", "automotive", "computer", "vision"}
    terms = [term for term in requirement.keywords if term.lower() not in generic]
    return not terms or any(contains(text, term) for term in terms)
