from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
ENV_EXAMPLE = ROOT / "docker" / "web-backend" / ".env.example"
README = ROOT / "docker" / "web-backend" / "README.md"
DOCKERFILE = ROOT / "docker" / "web-backend" / "Dockerfile"
COMPOSE = ROOT / "docker" / "web-backend" / "docker-compose.yml"
DEPLOY = ROOT / "docker" / "web-backend" / "deploy.sh"


class DeploymentContractTests(unittest.TestCase):
    def test_env_example_targets_baota_mysql_and_api_runtime(self):
        text = ENV_EXAMPLE.read_text(encoding="utf-8")

        self.assertIn(
            "DATABASE_URL=mysql+pymysql://iot_server:iot_dev_password@host.docker.internal:3306/iot_server",
            text,
        )
        self.assertIn("EMQX_WEBHOOK_SECRET=hyrain_emqx_webhook_secret_example", text)
        self.assertIn("APP_PORT=8000", text)

    def test_readme_documents_baota_docker_deploy(self):
        text = README.read_text(encoding="utf-8")

        self.assertIn("宝塔", text)
        self.assertIn("Docker", text)
        self.assertIn("bash deploy.sh", text)
        self.assertIn("python -m app.init_db", text)
        self.assertIn("api.hyrain.xyz", text)
        self.assertIn("https://api.hyrain.xyz/api/iot/emqx/property", text)

    def test_init_db_entrypoint_exists(self):
        path = ROOT / "docker" / "web-backend" / "app" / "init_db.py"
        text = path.read_text(encoding="utf-8")

        self.assertIn("Base.metadata.create_all", text)
        self.assertIn("def main()", text)

    def test_docker_deploy_files_are_defined(self):
        dockerfile = DOCKERFILE.read_text(encoding="utf-8")
        compose = COMPOSE.read_text(encoding="utf-8")
        deploy = DEPLOY.read_text(encoding="utf-8")

        self.assertIn("FROM python:3.12-slim", dockerfile)
        self.assertIn('CMD ["uvicorn", "app.main:app"', dockerfile)
        self.assertIn("host.docker.internal:host-gateway", compose)
        self.assertIn('"127.0.0.1:${APP_PORT:-8000}:8000"', compose)
        self.assertIn("python -m app.init_db", deploy)
        self.assertIn("docker compose --env-file .env up -d --build", deploy)
