from .db import SessionLocal
from .db_models import Plan

# Mirrors the tiers that used to be hardcoded in
# frontend/dataset-ai-ui/app/pricing/page.tsx — that page now fetches from
# GET /plans instead. daily_search_limit is the actual enforced number
# (decided with the user: 10/day free, unlimited pro/enterprise) - the old
# hardcoded page only ever *said* "unlimited searches", it didn't enforce
# anything.
SEED_PLANS = [
    {
        "name": "free",
        "display_name": "Free",
        "price_label": "$0",
        "period": None,
        "description": "For students and individuals exploring datasets.",
        "features": [
            "Natural-language dataset search",
            "Curated dataset catalog",
            "Basic Kaggle search",
            "Rule-based fallback when LLM is unavailable",
            "Personalized recommendations from your search history (sign in)",
            "10 searches/day",
        ],
        "daily_search_limit": 10,
    },
    {
        "name": "pro",
        "display_name": "Pro",
        "price_label": "$19",
        "period": "/month",
        "description": "For researchers and ML practitioners who search often.",
        "features": [
            "Everything in Free",
            "Priority Gemini-powered understanding",
            "Unlimited searches",
            "Multi-source discovery (Kaggle + OpenML + HuggingFace)",
            "Email support",
        ],
        "daily_search_limit": None,
    },
    {
        "name": "enterprise",
        "display_name": "Enterprise",
        "price_label": "Custom",
        "period": None,
        "description": "For labs and teams with private datasets and SLAs.",
        "features": [
            "Everything in Pro",
            "Team seats & shared workspaces",
            "Private/internal dataset integration",
            "API access",
            "Dedicated support & SLA",
        ],
        "daily_search_limit": None,
    },
]


def seed_plans_if_empty() -> None:
    """Same pattern as discovery_agent/seed.py: only fills a genuinely
    empty table, never overwrites admin changes (including an admin having
    deleted a seed plan on purpose)."""
    db = SessionLocal()
    try:
        if db.query(Plan).first() is not None:
            return

        for entry in SEED_PLANS:
            db.add(Plan(**entry))
        db.commit()
    finally:
        db.close()
