"""Regresiones del verificador en un checkout nuevo, sin iniciar el navegador."""
import importlib.util
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


class StopBeforeBrowser(Exception):
    pass


class DefenseToolTests(unittest.TestCase):
    def test_unlabelled_existing_volume_prevents_initialization(self):
        path = Path(__file__).with_name("defense_demo.py")
        spec = importlib.util.spec_from_file_location("defense_driver_test", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = "lizardjudge-defensa-colision"
            def docker_output(command, **kwargs):
                return project+"_backend\n" if "--format" in command else ""
            with patch.object(module, "ROOT", root), patch.object(module.subprocess, "check_output", side_effect=docker_output), \
                    patch.object(module, "run") as mutate, patch.object(sys, "argv", [str(path), "init", "--project", project]), \
                    self.assertRaises(SystemExit):
                module.main()
            mutate.assert_not_called()
            self.assertFalse((root / ".verification").exists())

    def test_evidence_parents_are_created_in_a_fresh_checkout(self):
        path = Path(__file__).with_name("verify_defense_demo.py")
        spec = importlib.util.spec_from_file_location("verify_defense_test", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = "lizardjudge-defensa-fixture"
            state = root / ".verification/runtime/defensa" / project / "state.json"
            state.parent.mkdir(parents=True)
            state.write_text(json.dumps({"port": 18084}))
            with patch.object(module, "ROOT", root), patch.object(module, "sync_playwright", side_effect=StopBeforeBrowser), \
                    patch.object(sys, "argv", [str(path), "--project", project]), self.assertRaises(StopBeforeBrowser):
                module.main()
            self.assertTrue((root / "respaldos/runtime" / project).is_dir())


if __name__ == "__main__":
    unittest.main()
