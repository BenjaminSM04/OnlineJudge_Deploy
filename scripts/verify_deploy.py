"""Ensayo aislado de arranque, conservación, respaldo y restauración lógica."""

import argparse
import hashlib
import json
import os
import secrets
from pathlib import Path
import subprocess
import sys
import tarfile
import urllib.request


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    if not args.project.startswith("lizardjudge-verificacion-"):
        parser.error("Use un proyecto nuevo con prefijo lizardjudge-verificacion-.")
    os.environ.setdefault("VERIFY_DATABASE_PASSWORD", secrets.token_urlsafe(32))
    os.environ.setdefault("VERIFY_JUDGE_TOKEN", secrets.token_urlsafe(32))
    compose = ["docker", "compose", "-p", args.project, "-f", str(ROOT / "compose.verify.yml")]

    def run(command, **kwargs):
        return subprocess.run(command, cwd=ROOT, check=True, **kwargs)

    def app(code):
        result = run(compose + ["exec", "-T", "oj-backend", "python", "manage.py", "shell"],
                     input=code, encoding="utf-8", stdout=subprocess.PIPE)
        return result.stdout.strip().splitlines()[-1]

    backup_dir = ROOT / "respaldos" / args.project
    db_args = ["--project", args.project, "--compose-file", str(ROOT / "compose.verify.yml"),
               "--directory", str(backup_dir), "--writers-stopped"]
    try:
        failure_env = dict(os.environ, POSTGRES_PASSWORD=secrets.token_urlsafe(32),
                           JUDGE_SERVER_TOKEN=secrets.token_urlsafe(32))
        failure = subprocess.run(["docker", "run", "--rm", "--network", "none", "-e", "POSTGRES_HOST=127.0.0.1",
                                  "-e", "POSTGRES_DB=onlinejudge", "-e", "POSTGRES_USER=onlinejudge",
                                  "-e", "POSTGRES_PASSWORD", "-e", "JUDGE_SERVER_TOKEN",
                                  "-e", "MAX_WORKER_NUM=2", "lizardjudge-revision:local"],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=failure_env)
        assert failure.returncode == 1 and b"Se cancela el arranque" in failure.stdout, "El arranque no falló cerrado."
        run(compose + ["up", "-d", "--wait", "--wait-timeout", "120", "oj-postgres", "oj-postgres17", "oj-redis"])
        run(compose + ["up", "-d", "--wait", "--wait-timeout", "120", "oj-backend"])
        run(compose + ["exec", "-T", "oj-backend", "python", "manage.py", "check"])
        run(compose + ["exec", "-T", "oj-backend", "python", "manage.py", "test",
                       "ai_tutor", "utils.test_inituser", "--noinput", "--verbosity", "0"])
        app('from account.models import User; assert User.objects.count() == 0; print("Sin administrador automático")')
        fixture = '''
import copy, hashlib, json, secrets
from pathlib import Path
from django.core.management import call_command
from account.models import User
from problem.tests import DEFAULT_PROBLEM_DATA, ProblemCreateTestBase
from submission.models import Submission
from ai_tutor.models import TutorSession, TutorAttempt
from ai_tutor.tests.config_factory import create_active_config
call_command("inituser", username="admin-ensayo", password=secrets.token_urlsafe(32), action="create_super_admin")
user = User.objects.get(username="admin-ensayo")
data = copy.deepcopy(DEFAULT_PROBLEM_DATA)
data.update(title="Conservación: ñ y fórmulas", samples=[{"input": "1\\n", "output": "2\\n"}])
problem = ProblemCreateTestBase.add_problem(data, user)
version = create_active_config(problem, user)
session = TutorSession.objects.create(user=user, problem=problem, config_version=version)
submission = Submission.objects.create(user_id=user.id, username=user.username, problem=problem,
    code="print(2)\\n", language="Python3", result=0, statistic_info={"time_cost": 1, "memory_cost": 1024})
TutorAttempt.objects.create(session=session, submission=submission, language=submission.language, result=0)
Path("/data/public/upload/conservacion.txt").write_text("Archivo sintético: ñ\\n", encoding="utf-8")
print(json.dumps({"password": hashlib.sha256(user.password.encode()).hexdigest(),
                  "key": hashlib.sha256(Path("/data/config/secret.key").read_bytes()).hexdigest()}))
'''
        before = json.loads(app(fixture))
        for route in ("/", "/admin/", "/api/website"):
            with urllib.request.urlopen("http://127.0.0.1:" + os.environ.get("VERIFY_HTTP_PORT", "18080") + route, timeout=15) as response:
                assert response.status == 200, route
        run(compose + ["restart", "oj-backend"])
        run(compose + ["up", "-d", "--wait", "--wait-timeout", "120", "oj-backend"])
        after = json.loads(app('''
import hashlib, json
from pathlib import Path
from account.models import User
from submission.models import Submission
from ai_tutor.models import TutorAttempt
user = User.objects.get(username="admin-ensayo")
assert User.objects.count() == 1 and Submission.objects.count() == 1 and TutorAttempt.objects.count() == 1
assert Path("/data/public/upload/conservacion.txt").read_text(encoding="utf-8") == "Archivo sintético: ñ\\n"
print(json.dumps({"password": hashlib.sha256(user.password.encode()).hexdigest(),
                  "key": hashlib.sha256(Path("/data/config/secret.key").read_bytes()).hexdigest()}))
'''))
        assert before == after, "El reinicio alteró una contraseña o la clave existente."
        run(compose + ["stop", "oj-backend"])
        run([sys.executable, "backup/database.py", "backup"] + db_args)
        container = subprocess.check_output(compose + ["ps", "-a", "-q", "oj-backend"], text=True).strip()
        archive = backup_dir / "backend-data.tar.gz"
        run([sys.executable, "backup/files_backup.py", "--container", container, "--output", str(archive)])
        with tarfile.open(archive) as backup:
            assert hashlib.sha256(backup.extractfile("./config/secret.key").read()).hexdigest() == before["key"]
            assert backup.extractfile("./public/upload/conservacion.txt").read().decode() == "Archivo sintético: ñ\n"
        run([sys.executable, "backup/database.py", "restore"] + db_args)
        result = subprocess.run([sys.executable, "backup/database.py", "restore"] + db_args, cwd=ROOT)
        assert result.returncode != 0, "Se permitió sobrescribir un destino poblado."
        dump = backup_dir / "database.dump"
        size = dump.stat().st_size
        with dump.open("ab") as stream:
            stream.write(b"respaldo-alterado")
        try:
            result = subprocess.run([sys.executable, "backup/database.py", "verify"] + db_args, cwd=ROOT)
            assert result.returncode != 0, "Se aceptó un respaldo alterado."
        finally:
            with dump.open("r+b") as stream:
                stream.truncate(size)
        run([sys.executable, "backup/database.py", "verify"] + db_args)
        print("OK: arranque, pruebas, reinicio sin pérdida, archivos y restauración PostgreSQL 10 a 17.")
    finally:
        # Conservar los volúmenes y la evidencia para inspección posterior.
        run(compose + ["stop"])


if __name__ == "__main__":
    main()
