import unittest
from pathlib import Path
from sqlalchemy import create_engine, text

from security.database_config import database_url


class DatabaseConfigTests(unittest.TestCase):
    def test_local_sqlite_default(self):
        url = database_url(None, Path("/tmp/synthetic/app.db"))
        self.assertEqual(url.drivername, "sqlite")
        self.assertEqual(Path(url.database), Path("/tmp/synthetic/app.db"))

    def test_provider_urls_select_installed_psycopg_driver(self):
        for scheme in ("postgres", "postgresql", "postgresql+psycopg"):
            url = database_url(f"{scheme}://test:p%40ss%2Fword@db.example/test?sslmode=require&channel_binding=require", Path("unused"), vercel=True)
            self.assertEqual(url.drivername, "postgresql+psycopg")
            self.assertEqual(url.password, "p@ss/word")
            self.assertEqual(dict(url.query), {"sslmode": "require", "channel_binding": "require"})

    def test_cloud_missing_or_ephemeral_database_rejected(self):
        for value in (None, "", "sqlite:///:memory:", "sqlite:////tmp/app.db"):
            with self.assertRaises(ValueError): database_url(value, Path("unused"), vercel=True)

    def test_invalid_url_has_generic_error(self):
        with self.assertRaises(ValueError) as error:
            database_url("invalid synthetic secret", Path("unused"))
        self.assertNotIn("synthetic secret", str(error.exception))

    def test_sqlite_override_preserved_locally(self):
        engine = create_engine(database_url("sqlite:///:memory:", Path("unused")))
        try:
            with engine.connect() as connection:
                self.assertEqual(connection.execute(text("PRAGMA database_list")).one()[2], "")
        finally:
            engine.dispose()
