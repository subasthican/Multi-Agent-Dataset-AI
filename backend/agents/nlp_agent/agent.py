import spacy


nlp = spacy.load(
    "en_core_web_sm"
)


def analyze_query(text):

    doc = nlp(text)


    keywords=[]

    for token in doc:

        if token.pos_ in [
            "NOUN",
            "PROPN"
        ]:
            keywords.append(
                token.text
            )


    domain="general"

    domains=[
        "healthcare",
        "finance",
        "education",
        "business",
        "environment"
    ]


    for d in domains:
        if d in text.lower():
            domain=d


    return {

        "original_query":text,

        "domain":domain,

        "keywords":keywords,

        "task":"machine learning dataset"

    }
