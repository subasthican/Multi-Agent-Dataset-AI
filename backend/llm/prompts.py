def dataset_prompt(query: str) -> str:
    return f"""You are an AI dataset discovery assistant.

Analyze the user's requirement and extract:
1. domain (one or two words, e.g. "healthcare", "finance")
2. task (the machine learning task, e.g. "classification", "regression")
3. keywords (a short list of important terms)
4. data_type (one of: tabular, image, text, time_series)

Respond with ONLY a JSON object with exactly these keys:
domain, task, keywords, data_type

User request:
{query}
"""
