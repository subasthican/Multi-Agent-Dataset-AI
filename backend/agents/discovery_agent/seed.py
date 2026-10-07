import json
from pathlib import Path

from security.db import SessionLocal, lock_seed
from security.db_models import CatalogDataset

SEED_DATA_PATH = Path(__file__).parent / "datasets.json"


def seed_catalog_if_empty() -> None:
    """Seed an empty catalog and backfill missing links on unchanged seeds."""
    db = SessionLocal()
    try:
        lock_seed(db, 682409112)
        with open(SEED_DATA_PATH, "r", encoding="utf-8") as seed_file:
            seed_datasets = json.load(seed_file)
        if db.query(CatalogDataset).first() is not None:
            # Backfill links only for unchanged original seeds; preserve admin edits.
            for entry in seed_datasets:
                rows = db.query(CatalogDataset).filter_by(
                    name=entry["name"], description=entry["description"],
                    domain=entry["domain"], task=entry["task"], url=None,
                ).all()
                for row in rows:
                    row.url = entry.get("url")
            db.commit()
            return

        for entry in seed_datasets:
            db.add(
                CatalogDataset(
                    name=entry["name"],
                    description=entry["description"],
                    domain=entry["domain"],
                    task=entry["task"],
                    data_type=entry.get("data_type", "tabular"),
                    url=entry.get("url"),
                )
            )
        db.commit()
    finally:
        db.close()
