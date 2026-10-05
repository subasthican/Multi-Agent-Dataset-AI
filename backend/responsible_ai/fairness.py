"""Descriptive representation diagnostics; never certify fairness from counts."""
from collections import Counter


def representation_summary(results):
    return {
        "source_counts": dict(Counter(item.dataset.source for item in results)),
        "domain_counts": dict(Counter(item.dataset.domain for item in results)),
        "assessment": "Descriptive coverage only; fairness requires reviewed comparative evaluation.",
    }
