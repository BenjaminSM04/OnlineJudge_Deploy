"""Evalúa base y ajustado sobre test sintético; no mide aprendizaje ni aprobación humana."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "OnlineJudge"))
CPU = "ghcr.io/ggml-org/llama.cpp:server@sha256:8c74db29f1a2bef3f0a331b52c4d6214601dfceed4bee0b94cc48b3b23ff257d"
GPU = "ghcr.io/ggml-org/llama.cpp@sha256:490d8cd8000203a3ab8fdfce14ef931e2aa85affd4dd4447bcc75f299f00fd9a"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("base_gguf", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--mode", choices=("cpu", "gpu"), default="gpu")
    parser.add_argument("--runtime-name", default="runtime")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("La salida ya existe; se conserva.")
    from django.conf import settings
    if not settings.configured:
        settings.configure(USE_I18N=False, USE_TZ=True, INSTALLED_APPS=[])
    import django
    django.setup()
    from ai_tutor.dataset.pipeline import load_dataset, sha
    from ai_tutor.ml.prompt import build_messages, training_messages
    from ai_tutor.ml.runtime import predict
    from ai_tutor.services.output_guard import validate_output
    from utils.bounded_http import post_json
    parts, manifest = load_dataset(args.directory / "dataset", technical_demo=True)
    classifier = json.loads((args.directory / "classifier.json").read_text(encoding="utf-8"))
    reports = []
    for label, path in (("base", args.base_gguf), ("qlora", args.directory / args.runtime_name / "model.gguf")):
        name = "lizardjudge-eval-" + uuid.uuid4().hex[:10]
        command = ["docker", "run", "-d", "--name", name, "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
                   "--pids-limit", "64", "--memory", "4g" if args.mode == "gpu" else "3g", "--cpus", "2", "--tmpfs", "/tmp:size=64m",
                   "-p", "127.0.0.1::8080", "--mount", "type=bind,source="+str(path.resolve())+",target=/models/model.gguf,readonly"]
        if args.mode == "gpu":
            command += ["--gpus", "all"]
        command += [GPU if args.mode == "gpu" else CPU, "-m", "/models/model.gguf", "--host", "0.0.0.0", "--port", "8080", "-c", "4096", "-np", "1", "--threads", "2"]
        if args.mode == "gpu":
            command += ["-ngl", "99"]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL)
        try:
            info = json.loads(subprocess.check_output(["docker", "inspect", name], text=True))[0]
            port = info["NetworkSettings"]["Ports"]["8080/tcp"][0]["HostPort"]
            url = "http://127.0.0.1:" + port
            ready = False
            for _ in range(180):
                try:
                    with urllib.request.urlopen(url + "/health", timeout=1) as response:
                        if response.status == 200:
                            ready = True
                            break
                except Exception:
                    time.sleep(1)
            if not ready:
                raise RuntimeError("El modelo no quedó disponible.")
            rows = []
            for index, item in enumerate(parts["test"]):
                level = index % 3 + 1
                data = json.loads(training_messages(item, level)[1]["content"])
                category, confidence = predict(classifier, item)
                messages = build_messages(data["context"], {"category": category, "confidence": confidence})
                started = time.monotonic()
                row = {"example_id": item["example_id"], "level": level, "json_valid": False, "guard_accepted": False}
                try:
                    result = post_json(url+"/v1/chat/completions", json.dumps({"messages": messages, "max_tokens": 400,
                                       "temperature": 0, "seed": 2026, "response_format": {"type": "json_object"}}).encode(), 30, max_bytes=64000)
                    raw = result["choices"][0]["message"]["content"]
                    row["response"] = raw
                    generated = json.loads(raw)
                    row["json_valid"] = True
                    generated["model_version"] = "fixture-evaluation"
                    validate_output(generated)
                    row["guard_accepted"] = True
                    target = item["hints"][("concept", "location", "strategy")[level-1]]
                    row["synthetic_target_exact_match"] = generated["content"].strip() == target.strip()
                except Exception as error:
                    row["error_type"] = type(error).__name__
                row["latency_ms"] = round((time.monotonic()-started)*1000, 2)
                rows.append(row)
                print(label, row["example_id"], "JSON", row["json_valid"], "guard", row["guard_accepted"], flush=True)
            values = sorted(row["latency_ms"] for row in rows)
            reports.append({"model": label, "model_sha256": sha(path), "samples": len(rows), "json_valid": sum(row["json_valid"] for row in rows),
                            "guard_accepted": sum(row["guard_accepted"] for row in rows), "synthetic_target_exact_matches": sum(row.get("synthetic_target_exact_match", False) for row in rows),
                            "p50_ms": statistics.median(values), "p95_ms": values[max(0,(len(values)*95+99)//100-1)], "responses": rows})
        finally:
            subprocess.run(["docker", "rm", "-f", name], check=True, stdout=subprocess.DEVNULL)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump({"scope": "technical-demo", "human_review": "not-performed", "evaluation": "held-out-synthetic",
                   "dataset_version": manifest["version"], "mode": args.mode, "llama_image": GPU if args.mode == "gpu" else CPU,
                   "date_utc": datetime.now(timezone.utc).isoformat(), "reports": reports,
                   "limits": "Los checks de formato y guard no miden corrección pedagógica ni aprendizaje."}, stream, indent=2, ensure_ascii=True)


if __name__ == "__main__":
    main()
