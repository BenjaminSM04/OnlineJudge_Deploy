"""Exige CI verde del SHA exacto antes de integrar punteros de main."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPOS = {"OnlineJudge": "BenjaminSM04/PS2B2026-JuezVirtual_Backend",
         "OnlineJudgeFE": "BenjaminSM04/PS2B2026-JuezVirtual_frontend"}


def main():
    manifest = {}
    for folder, repository in REPOS.items():
        sha = subprocess.check_output(["git", "-C", str(ROOT / folder), "rev-parse", "HEAD"], text=True).strip()
        runs = json.loads(subprocess.check_output(["gh", "api", f"repos/{repository}/commits/{sha}/check-runs?per_page=100"]))["check_runs"]
        candidates = [run for run in runs if run["name"] == "validar" and run["app"]["slug"] == "github-actions" and run["head_sha"] == sha]
        latest = max(candidates, key=lambda run: run["id"]) if candidates else None
        if not latest or latest["status"] != "completed" or latest["conclusion"] != "success":
            raise SystemExit(f"Falta CI validar aprobada para {folder} {sha}; no se publica el puntero.")
        # Respetar el último intento de cada comprobación, incluido el escáner de secretos.
        checks = {}
        for run in sorted(runs, key=lambda item: item["id"]):
            checks[(run["name"], run["app"]["slug"])] = run
        if any(run["status"] != "completed" or run["conclusion"] in {"failure", "timed_out", "action_required", "cancelled"} for run in checks.values()):
            raise SystemExit(f"Hay comprobaciones pendientes o rechazadas para {folder} {sha}.")
        manifest[folder] = {"repository": repository, "sha": sha, "check": latest["html_url"]}
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
