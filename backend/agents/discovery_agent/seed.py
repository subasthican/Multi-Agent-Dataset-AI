import json
from pathlib import Path

from security.db import SessionLocal
from security.db_models import CatalogDataset

SEED_DATA_PATH = Path(__file__).parent / "datasets.json"


def seed_catalog_if_empty() -> None:
    """Runs on every startup, but only actually does anything once: if the
    catalog table already has any rows — including an admin having deleted
    every seed entry on purpose — this does nothing. It never overwrites
    admin changes, it only fills a genuinely empty table on first run."""
    db = SessionLocal()
    try:
        if db.query(CatalogDataset).first() is not None:
            return

        with open(SEED_DATA_PATH, "r", encoding="utf-8") as seed_file:
            seed_datasets = json.load(seed_file)

        for entry in seed_datasets:
            db.add(
                CatalogDataset(
                    name=entry["name"],
                    description=entry["description"],
                    domain=entry["domain"],
                    task=entry["task"],
                )
            )
        db.commit()
    finally:
        db.close()
