"""Carga local del fallback con sesiones sintéticas; no evalúa un modelo ni el servidor."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from http.cookies import SimpleCookie
import json
from pathlib import Path
import platform
import statistics
import subprocess
import time
import urllib.request
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    if not args.project.startswith("lizardjudge-upgrade-"):
        parser.error("Solo proyectos de ensayo aislados.")
    compose = ["docker", "compose", "-p", args.project, "-f", "compose.upgrade-verify.yml"]
    identifier = "LOAD-" + uuid.uuid4().hex[:10]
    seed = '''
import os,json,secrets
assert os.environ.get("OJ_VERIFICATION_ONLY")=="1"
from account.models import User,UserProfile
from problem.tests import DEFAULT_PROBLEM_DATA,ProblemCreateTestBase
from ai_tutor.models import TutorProblemConfig
from ai_tutor.tests.config_factory import create_active_config
from ai_tutor.services.sessions import create_or_recover
from submission.models import Submission
from django.contrib.sessions.backends.cache import SessionStore
owner=User.objects.get(username="ensayo-historico")
problem=ProblemCreateTestBase.add_problem(dict(DEFAULT_PROBLEM_DATA,_id="''' + identifier + '''"),owner)
create_active_config(problem,owner);TutorProblemConfig.objects.create(problem=problem,enabled=True)
rows=[]
for index in range(4):
    user=User(username="''' + identifier + '''-"+str(index));user.set_password(secrets.token_urlsafe(32));user.save();UserProfile.objects.create(user=user)
    session=create_or_recover(user,problem.id)
    Submission.objects.create(user_id=user.id,username=user.username,problem=problem,language="Python3",code="print(0)",result=-1)
    store=SessionStore();store["_auth_user_id"]=str(user.id);store["_auth_user_backend"]="django.contrib.auth.backends.ModelBackend";store["_auth_user_hash"]=user.get_session_auth_hash();store.save()
    user.session_keys=[store.session_key];user.save();rows.append({"session":str(session.id),"cookie":store.session_key})
print(json.dumps(rows))
'''
    raw = subprocess.check_output(compose + ["exec", "-T", "oj-backend", "python", "manage.py", "shell", "--verbosity", "0"], input=seed, encoding="utf-8")
    users = json.loads(raw.strip().splitlines()[-1])
    root = "http://127.0.0.1:18082"

    def run(user):
        cookie = "sessionid=" + user["cookie"]
        with urllib.request.urlopen(urllib.request.Request(root + "/api/profile", headers={"Cookie": cookie}), timeout=5) as response:
            jar = SimpleCookie()
            for value in response.headers.get_all("Set-Cookie", []):
                jar.load(value)
            csrf = jar["csrftoken"].value
        cookie += "; csrftoken=" + csrf
        rows = []
        for index in range(7):
            body = json.dumps({"session_id": user["session"], "request_id": str(uuid.uuid4()), "action": "explain"}).encode()
            request = urllib.request.Request(root + "/api/ai_tutor/feedback", body,
                {"Cookie": cookie, "X-CSRFToken": csrf, "Content-Type": "application/json"})
            started = time.monotonic()
            with urllib.request.urlopen(request, timeout=8) as response:
                result = json.load(response)
            elapsed = (time.monotonic() - started) * 1000
            if index < 6:
                assert result["error"] is None and result["data"]["source"] == "deterministic", result.get("error")
                rows.append(elapsed)
            else:
                assert result["error"] == "tutor-rate-limit"
        return rows

    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=4) as pool:
        values = sorted(value for rows in pool.map(run, users) for value in rows)
    duration = time.monotonic() - started
    memory = subprocess.check_output(["docker", "stats", "--no-stream", "--format", "{{.MemUsage}}", args.project + "-oj-backend-1"], text=True).strip()
    report = {"scope": "local-fallback-only", "platform": platform.platform(), "production_access": False,
        "model_inference": False, "concurrency": 4, "completed": len(values), "quota_denials_verified": 4,
        "seconds": round(duration, 3), "p50_ms": round(statistics.median(values), 2),
        "p95_ms": round(values[(len(values)*95+99)//100-1], 2), "max_ms": round(max(values), 2),
        "memory_sample_after_load": memory, "memory_peak": "not-measured"}
    path = Path("respaldos/runtime/load-fallback.json")
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
