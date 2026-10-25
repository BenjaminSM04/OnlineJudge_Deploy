"""Valida Compose sin arrancar servicios ni tocar almacenamiento real."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ProductionConfigTest(unittest.TestCase):
    def values(self):
        return {"POSTGRES_PASSWORD": secrets.token_urlsafe(32), "JUDGE_SERVER_TOKEN": secrets.token_urlsafe(32),
                "OJ_APP_IMAGE": "ghcr.io/benjaminsm04/lizardjudge:sha-" + "a" * 40, "OJ_PG17_VOLUME": "test-existing-pg17",
                "OJ_BACKEND_DATA": "/srv/test/backend", "OJ_REDIS_DATA": "/srv/test/redis",
                "OJ_JUDGE_LOG": "/srv/test/judge-log", "OJ_JUDGE_RUN": "/srv/test/judge-run",
                "ALLOWED_HOSTS": "lj.isilp.com", "CSRF_TRUSTED_ORIGINS": "https://lj.isilp.com"}

    def command(self, values):
        environment = {key: value for key, value in os.environ.items()
                       if not key.startswith(("OJ_", "POSTGRES_", "JUDGE_", "ALLOWED_HOSTS", "CSRF_TRUSTED_ORIGINS"))}
        environment.update(values)
        return subprocess.run(["docker", "compose", "--env-file", os.devnull, "-f", str(ROOT / "compose.produccion.yml"),
                               "config", "--format", "json"], env=environment, text=True, capture_output=True)

    def test_missing_environment_is_rejected(self):
        values = self.values()
        values.pop("POSTGRES_PASSWORD")
        result = self.command(values)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("POSTGRES_PASSWORD", result.stderr)

    def test_private_services_and_explicit_storage(self):
        config = self.command(self.values())
        self.assertEqual(config.returncode, 0, "No se pudo resolver el Compose con entorno sintético.")
        data = json.loads(config.stdout)
        self.assertTrue(data["volumes"]["pgdata17"]["external"])
        for name, service in data["services"].items():
            self.assertNotIn("build", service)
            if name != "oj-backend":
                self.assertFalse(service.get("ports"))
            for volume in service.get("volumes", []):
                if volume["type"] == "bind":
                    self.assertFalse(volume["bind"].get("create_host_path", False))
        backend = data["services"]["oj-backend"]
        self.assertEqual(backend["ports"][0]["host_ip"], "127.0.0.1")
        self.assertEqual(backend["environment"]["AI_TUTOR_MODEL_ENABLED"], "0")
        self.assertNotIn("OJ_VERIFICATION_ONLY", backend["environment"])
        self.assertTrue(data["networks"]["private"]["internal"])


if __name__ == "__main__":
    unittest.main()
