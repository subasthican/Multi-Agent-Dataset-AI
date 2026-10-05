import unittest

from agents.discovery_agent.identity import canonical_dataset_url, deduplicate_records


class DatasetIdentityTests(unittest.TestCase):
    def test_catalog_and_provider_copy_keep_catalog(self):
        catalog = {"source": "catalog", "id": "curated", "url": "https://www.kaggle.com/datasets/owner/data", "description": "curated"}
        live = {"source": "kaggle", "id": "owner/data", "url": "http://kaggle.com/datasets/owner/data/?utm_source=test#files", "description": "inferred"}
        self.assertEqual(deduplicate_records([catalog, live]), [catalog])

    def test_same_name_different_urls_remain_distinct(self):
        items = [{"source": "kaggle", "id": "one", "name": "diabetes", "url": "https://kaggle.com/datasets/a/one"},
                 {"source": "huggingface", "id": "two", "name": "diabetes", "url": "https://huggingface.co/datasets/a/two"}]
        self.assertEqual(deduplicate_records(items), items)

    def test_source_id_without_url(self):
        items = [{"source": "openml", "id": 37}, {"source": "openml", "id": "37"}, {"source": "catalog", "id": 37}]
        self.assertEqual(deduplicate_records(items), [items[0], items[2]])

    def test_missing_identity_is_not_merged(self):
        self.assertEqual(len(deduplicate_records([{"name": "same"}, {"name": "same"}])), 2)

    def test_identity_bridge_reconciles_transitively(self):
        items = [{"source": "catalog", "id": "curated", "url": "https://openml.org/d/37"},
                 {"source": "openml", "id": "openml-37"},
                 {"source": "openml", "id": "openml-37", "url": "https://www.openml.org/d/37/"}]
        self.assertEqual(deduplicate_records(items), [items[0]])

    def test_versions_and_functional_query_parameters_are_distinct(self):
        urls = ["https://kaggle.com/datasets/a/b?version=1", "https://kaggle.com/datasets/a/b?version=2",
                "https://huggingface.co/datasets/a/b/tree/main", "https://huggingface.co/datasets/a/b/tree/v2"]
        items = [{"source": "catalog", "id": str(i), "url": u} for i, u in enumerate(urls)]
        self.assertEqual(len(deduplicate_records(items)), 4)

    def test_generic_site_scheme_path_and_query_order_preserved(self):
        pairs = [("https://example.com/data", "http://example.com/data"),
                 ("https://example.com/data", "https://example.com/data/"),
                 ("https://example.com/Data", "https://example.com/data"),
                 ("https://example.com/data?a=1&b=2", "https://example.com/data?b=2&a=1")]
        for a, b in pairs:
            self.assertNotEqual(canonical_dataset_url(a), canonical_dataset_url(b))

    def test_default_ports_tracking_and_fragments(self):
        self.assertEqual(canonical_dataset_url("https://WWW.OPENML.ORG:443/d/37/?utm_campaign=test#download"), "https://openml.org/d/37")
        self.assertEqual(canonical_dataset_url("https://example.com:443/data?record=1&utm_source=test"), "https://example.com/data?record=1")

    def test_invalid_or_authenticated_urls_are_not_keys(self):
        for url in (None, "", "javascript:alert(1)", "https://example.com:bad/data", "https://user:password@example.com/data"):
            self.assertIsNone(canonical_dataset_url(url))

    def test_unknown_hash_routes_and_nondefault_provider_ports_remain_distinct(self):
        self.assertNotEqual(canonical_dataset_url("https://example.com/#/dataset/1"), canonical_dataset_url("https://example.com/#/dataset/2"))
        self.assertNotEqual(canonical_dataset_url("https://kaggle.com:80/datasets/a/b"), canonical_dataset_url("https://kaggle.com/datasets/a/b"))

    def test_inputs_not_mutated(self):
        item = {"source": "catalog", "id": "one", "url": "https://www.openml.org/d/37/"}
        copy = dict(item)
        result = deduplicate_records([item])
        result[0]["url"] = "changed"
        self.assertEqual(item, copy)
