import unittest
from unittest.mock import patch

from agents.dataset_collection_agent import agent


class CollectionIdentityTests(unittest.TestCase):
    def test_standalone_collection_reconciles_source_copies(self):
        fields = {"name": "Fixture", "description": "Medical diabetes classification table",
                  "domain": "healthcare", "task": "classification", "data_type": "tabular", "similarity": 0.9}
        first = {**fields, "source": "kaggle", "id": "a/b", "url": "https://kaggle.com/datasets/a/b"}
        copy = {**fields, "source": "huggingface", "id": "mirror", "url": "https://www.kaggle.com/datasets/a/b/?utm_source=test"}
        distinct = {**fields, "source": "openml", "id": "37", "url": "https://www.openml.org/d/37"}
        with patch.object(agent, "search_kaggle_datasets", return_value=[first]) as kaggle, \
             patch.object(agent, "search_openml_datasets", return_value=[distinct]) as openml, \
             patch.object(agent, "search_huggingface_datasets", return_value=[copy]) as huggingface:
            result = agent.collect_external_datasets("diabetes", limit=5)
        self.assertEqual(result, [first, distinct])
        kaggle.assert_called_once_with("diabetes", limit=2)
        for source in (openml, huggingface):
            source.assert_called_once_with("diabetes", 2)
