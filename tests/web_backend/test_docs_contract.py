from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class DocsContractTests(unittest.TestCase):
    def test_project_docs_reference_mysql_preview_flow(self):
        text = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")

        self.assertIn("EMQX Webhook", text)
        self.assertIn("device_latest_status", text)
        self.assertIn("docker/web-backend", text)
        self.assertIn("MySQL", text)
