import unittest
from unittest.mock import Mock, patch

from agents.nlp_agent.agent import analyze_query, classify_task
from agents.nlp_agent.models import QueryAnalysisResult
from agents.discovery_agent.models import DatasetMatch
from agents.evaluation_agent.agent import evaluate_datasets
from agents.recommendation_agent.agent import record_search, _build_profile
from agents.discovery_agent.seed import seed_catalog_if_empty
from security.db_models import CatalogDataset
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from agents.dataset_collection_agent.huggingface_source import search_huggingface_datasets
from responsible_ai.language import supported_english
from main import _external_query


class SearchFixTests(unittest.TestCase):
    def requirement(self, query="cancer prediction dataset", **fields):
        return QueryAnalysisResult(original_query=query, domain="healthcare", task="classification",
                                   data_type="tabular", keywords=["cancer", "prediction"], **fields)

    def dataset(self, name, **fields):
        return DatasetMatch(id=name, name=name, description=name + " clinical classification records",
                            domain="healthcare", task="classification", data_type="tabular", similarity=0.95, **fields)

    def test_short_english_and_non_english(self):
        self.assertTrue(supported_english("cancer image classification dataset"))
        self.assertTrue(supported_english("credit card fraud dataset"))
        self.assertFalse(supported_english("Je cherche des donnees pour predire le cancer"))

    def test_cancer_excludes_other_diseases(self):
        result = evaluate_datasets([self.dataset("Diabetes"), self.dataset("Heart disease"), self.dataset("Breast cancer")], self.requirement())
        self.assertEqual([r.dataset.name for r in result], ["Breast cancer"])

    def test_subject_first_external_search(self):
        self.assertEqual(_external_query(self.requirement()), "cancer")

    def test_fraud_classification_and_ambiguous_task(self):
        self.assertEqual(classify_task("credit card fraud", []), "classification")
        with patch("agents.nlp_agent.agent._understand_with_llm", return_value=None):
            result = analyze_query("healthcare datasets")
        self.assertTrue(result.needs_task_selection)
        self.assertEqual(evaluate_datasets([self.dataset("Healthcare")], result), [])

    def test_kidney_ultrasound_is_healthcare(self):
        with patch("agents.nlp_agent.agent._understand_with_llm", return_value=None):
            result = analyze_query("kidney ultrasound image classification dataset")
        self.assertEqual(result.domain, "healthcare")
        self.assertEqual(result.task, "computer_vision")
        self.assertEqual(result.data_type, "image")
        self.assertEqual(result.warnings, [])

    def test_unclear_history_not_recorded(self):
        db = Mock()
        record_search(db, Mock(), self.requirement(warnings=["Unclear request"]))
        db.add.assert_not_called()
        record_search(db, Mock(), self.requirement(needs_task_selection=True))
        db.add.assert_not_called()

    def test_external_metadata_required(self):
        dataset = self.dataset("Cancer", source="huggingface", url="https://huggingface.co/datasets/example/cancer")
        self.assertEqual(evaluate_datasets([dataset], self.requirement()), [])
        dataset.license = "cc-by-4.0"
        dataset.metadata_verified = True
        self.assertEqual(len(evaluate_datasets([dataset], self.requirement())), 1)
        dataset.task = "regression"
        self.assertEqual(evaluate_datasets([dataset], self.requirement()), [])

    def test_huggingface_uses_verified_card(self):
        listing = Mock(status_code=200)
        listing.json.return_value = [{"id": "example/cancer"}]
        detail = Mock()
        detail.json.return_value = {"description": "Cancer CT images with diagnostic labels", "tags": [],
                                    "cardData": {"license": "cc-by-4.0", "task_categories": ["image-classification"]}}
        with patch("agents.dataset_collection_agent.huggingface_source.requests.get", side_effect=[listing, detail]), \
             patch("agents.dataset_collection_agent.huggingface_source.rank_by_similarity", return_value=[0.9]):
            result = search_huggingface_datasets("cancer", 1)[0]
        self.assertTrue(result["metadata_verified"])
        self.assertEqual(result["data_type"], "image")
        self.assertEqual(result["task"], "computer_vision")
        self.assertEqual(result["license"], "cc-by-4.0")

    def test_seed_links_backfilled_without_overwriting_admin(self):
        import json
        from agents.discovery_agent.seed import SEED_DATA_PATH
        engine = create_engine("sqlite://")
        CatalogDataset.__table__.create(engine)
        entry = json.loads(SEED_DATA_PATH.read_text())[0]
        with Session(engine) as db:
            seed = CatalogDataset(name=entry["name"], description=entry["description"], domain=entry["domain"], task=entry["task"], data_type="tabular")
            edited = CatalogDataset(name="Admin dataset", description="Custom", domain="finance", task="classification", url="https://example.org/custom")
            db.add_all([seed, edited])
            db.commit()
            seed_id, edited_id = seed.id, edited.id
            with patch("agents.discovery_agent.seed.SessionLocal", return_value=db), patch("agents.discovery_agent.seed.lock_seed"):
                seed_catalog_if_empty()
            self.assertEqual(db.get(CatalogDataset, seed_id).url, entry["url"])
            self.assertEqual(db.get(CatalogDataset, edited_id).url, "https://example.org/custom")
        engine.dispose()

    def test_legacy_unclear_history_excluded_in_query(self):
        db = Mock()
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        self.assertEqual(_build_profile(db, Mock()), (None, None, 0))
        self.assertEqual(db.query.return_value.filter.return_value.filter.call_count, 1)


if __name__ == "__main__":
    unittest.main()
