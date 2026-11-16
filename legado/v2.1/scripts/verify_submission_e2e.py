"""Envío real desde Chromium, cola Dramatiq, juez aislado y progreso personal."""
import argparse
import json
import os
import re
from pathlib import Path
import subprocess
import time
import uuid

from playwright.sync_api import sync_playwright, expect
from verify_judge import IMAGE, SOURCES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    if not args.project.startswith("lizardjudge-upgrade-"):
        parser.error("Solo proyectos de ensayo.")
    compose = ["docker", "compose", "-p", args.project, "-f", "compose.upgrade-verify.yml"]
    def backend(code):
        raw = subprocess.check_output(compose + ["exec", "-T", "oj-backend", "python", "manage.py", "shell", "--verbosity", "0"],
            input='import os; assert os.environ.get("OJ_VERIFICATION_ONLY")=="1"\n' + code, encoding="utf-8")
        return json.loads(raw.strip().splitlines()[-1])
    identifier = "REAL-" + uuid.uuid4().hex[:10]
    fixture = backend('''
import json,secrets,hashlib
from pathlib import Path
from account.models import User,UserProfile
from problem.tests import DEFAULT_PROBLEM_DATA,ProblemCreateTestBase
from django.contrib.sessions.backends.cache import SessionStore
from django.core.management import call_command
call_command("update_go_compiler_budget",apply=True)
owner=User.objects.get(username="ensayo-historico")
user=User(username="''' + identifier + '''");user.set_password(secrets.token_urlsafe(32));user.save();UserProfile.objects.create(user=user,language="es-LA")
case_id="''' + uuid.uuid4().hex + '''"
directory=Path('/data/test_case')/case_id;directory.mkdir(mode=0o755)
(directory/'1.in').write_text('2 3\\n');(directory/'1.out').write_text('5\\n')
info={"spj":False,"test_case_number":1,"test_cases":{"1":{"input_name":"1.in","output_name":"1.out","input_size":4,"output_size":2,"output_md5":hashlib.md5(b'5\\n').hexdigest(),"stripped_output_md5":hashlib.md5(b'5').hexdigest()}}}
(directory/'info').write_text(json.dumps(info))
problem=ProblemCreateTestBase.add_problem(dict(DEFAULT_PROBLEM_DATA,_id="''' + identifier + '''",languages=list(''' + repr(list(SOURCES)) + '''),test_case_id=case_id,samples=[{"input":"2 3","output":"5"}]),owner)
store=SessionStore();store["_auth_user_id"]=str(user.id);store["_auth_user_backend"]="django.contrib.auth.backends.ModelBackend";store["_auth_user_hash"]=user.get_session_auth_hash();store.save();user.session_keys=[store.session_key];user.save()
print(json.dumps({"cookie":store.session_key,"token":os.environ['JUDGE_SERVER_TOKEN']}))
''')
    container = args.project + "-oj-backend-1"
    info = json.loads(subprocess.check_output(["docker", "inspect", container], text=True))[0]
    volume = next(m["Name"] for m in info["Mounts"] if m["Destination"] == "/data")
    network = "lizardjudge-e2e-" + uuid.uuid4().hex[:10]
    name = network + "-judge"
    subprocess.run(["docker", "network", "create", "--internal", network], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["docker", "network", "connect", "--alias", "oj-backend", network, container], check=True)
    environment = dict(os.environ, TOKEN=fixture["token"])
    command = ["docker", "run", "-d", "--name", name, "--network", network, "--network-alias", "oj-judge-e2e", "--read-only",
        "--pids-limit", "128", "--memory", "1g", "--cpus", "2", "--tmpfs", "/judger:size=256m,exec", "--tmpfs", "/log:size=16m", "--tmpfs", "/tmp:size=256m,exec",
        "--mount", "type=volume,source=" + volume + ",target=/test_case,volume-subpath=test_case,readonly", "-e", "TOKEN",
        "-e", "SERVICE_URL=http://oj-judge-e2e:8080", "-e", "BACKEND_URL=http://oj-backend:8000/api/judge_server_heartbeat/",
        "--cap-drop", "SETPCAP", "--cap-drop", "MKNOD", "--cap-drop", "NET_BIND_SERVICE", "--cap-drop", "SYS_CHROOT", "--cap-drop", "SETFCAP", "--cap-drop", "FSETID",
        "--entrypoint", "sh", IMAGE, "-c", "mkdir -p /judger/run /judger/spj; chown compiler:code /judger/run; chmod 711 /judger/run; cd /app; while true; do .venv/bin/python service.py; sleep 2; done & exec .venv/bin/gunicorn server:app --workers 1 --threads 2 --bind 0.0.0.0:8080 --error-logfile /log/gunicorn.log"]
    rows = []
    try:
        subprocess.run(command, env=environment, check=True, stdout=subprocess.DEVNULL)
        time.sleep(3)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            context = browser.new_context(viewport={"width": 1280, "height": 900})
            context.add_cookies([{"name": "sessionid", "value": fixture["cookie"], "url": "http://127.0.0.1:18082"}])
            page = context.new_page()
            for language, code in SOURCES.items():
                page.goto("http://127.0.0.1:18082/problem/" + identifier, wait_until="networkidle")
                selector = page.locator(".header .ivu-select").first
                selector.click()
                selector.locator(".ivu-select-item").filter(has_text=re.compile(r"^\s*" + re.escape(language) + r"\s*$")).click()
                page.evaluate("code => document.querySelector('.CodeMirror').CodeMirror.setValue(code)", code)
                started = time.monotonic()
                with page.expect_response(lambda response: response.url.endswith("/api/submission") and response.request.method == "POST") as created:
                    page.locator("#submit-code").get_by_role("button", name="Enviar").click()
                result = created.value.json()
                assert not result["error"], result["error"]
                submission_id = result["data"]["submission_id"]
                for _ in range(100):
                    result = context.request.get("http://127.0.0.1:18082/api/submission?id=" + submission_id).json()
                    if result["data"]["result"] not in (6, 7, 9):
                        break
                    page.wait_for_timeout(1000)
                assert result["data"]["result"] == 0, {"language": language, "result": result["data"]["result"], "diagnostic": result["data"].get("statistic_info")}
                rows.append({"language": language, "result": 0, "elapsed_ms": round((time.monotonic()-started)*1000)})
            page.goto("http://127.0.0.1:18082/", wait_until="networkidle")
            expect(page.locator(".personal-practice")).to_contain_text("1 problemas resueltos")
            page.screenshot(path="respaldos/runtime/submission-e2e.png", full_page=True)
            browser.close()
        Path("respaldos/runtime/submission-e2e.json").write_text(json.dumps({"image": IMAGE, "judge_network_internal": True,
            "browser_to_api_queue_judge": True, "synthetic_problem": True, "verdicts_seeded": False,
            "unique_achievement_count": 1, "results": rows}, indent=2), encoding="utf-8")
        print("OK: seis envíos reales desde Chromium por Dramatiq al juez; un logro único.")
    finally:
        subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.DEVNULL)
        subprocess.run(["docker", "network", "disconnect", network, container], stdout=subprocess.DEVNULL)
        subprocess.run(["docker", "network", "rm", network], stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
