"""Regresiones de integridad del motor, sin descargar ni aprobar modelos."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
for module, file in (("guard", "OnlineJudge/ai_tutor/services/output_guard.py"), ("classifier_runtime", "OnlineJudge/ai_tutor/ml/runtime.py"), ("tutor_server", "tutor_engine/server.py")):
    spec = importlib.util.spec_from_file_location(module, ROOT / file)
    instance = importlib.util.module_from_spec(spec)
    sys.modules[module] = instance
    spec.loader.exec_module(instance)
server = sys.modules["tutor_server"]


class IntegrityTests(unittest.TestCase):
    def test_only_exact_model_path_can_be_approved(self):
        with TemporaryDirectory() as temp:
            server.ROOT = Path(temp)
            approved = server.ROOT / "approved"
            approved.mkdir()
            (approved / "model.gguf").write_bytes(b"synthetic-reviewed-fixture")
            (server.ROOT / "model.gguf").write_bytes(b"synthetic-unreviewed-fixture")
            classifier = server.ROOT / "classifier.json"
            classifier.write_text(json.dumps({"dataset_version": "fixture"}))
            entry = lambda p: {"file": str(p.relative_to(server.ROOT)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            manifest = {"decision": "integrate", "reviewer": "fixture-reviewer", "trained_by": "fixture-author", "reviewed_at": "2026-01-01", "license": "fixture", "model_revision": "fixture", "dataset_version": "fixture", "generator": entry(approved / "model.gguf"), "classifier": entry(classifier)}
            (server.ROOT / "manifest.json").write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                server.load_artifacts()

    def test_inline_and_multiline_programs_are_rejected(self):
        for text in ('a,b=map(int,open(0).read().split()); print(a+b)',
                     'x = __import__("sys").stdin.read(); __import__("sys").stdout.write(str(sum(map(int,x.split()))))',
                     'a,b=map(int,open(0).read().split())\nprint(a+b)',
                     'Observa el siguiente paso: console.log(a + b)',
                     'Revisa esto: System.out.println(a+b);'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                server.validate_output({"content": text, "uncertainty": "", "model_version": "fixture"})


if __name__ == "__main__":
    unittest.main()
