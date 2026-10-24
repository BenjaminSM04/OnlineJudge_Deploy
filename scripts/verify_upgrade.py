"""Actualización aislada con datos desde el backend histórico; nunca usa el servidor."""
import argparse
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backup"))
from database import Database, identifier  # noqa: E402

LEGACY = "72fc56327644e8a48e350c40a383a7949b984217"


def run(command, **kwargs):
    return subprocess.run(command, cwd=ROOT, check=True, **kwargs)


def export_legacy():
    path = ROOT / ".verification/legacy-backend"
    git = ["git", "-c", "safe.directory=" + str(ROOT / "OnlineJudge"), "-C", str(ROOT / "OnlineJudge")]
    archive = subprocess.check_output(git + ["archive", "--format=tar", LEGACY])
    if path.exists():
        with tarfile.open(fileobj=BytesIO(archive)) as files:
            for item in files:
                if item.isfile() and (path / item.name).read_bytes() != files.extractfile(item).read():
                    raise ValueError("La copia histórica cambió; use otro directorio de verificación.")
        return
    path.mkdir(parents=True)
    with tarfile.open(fileobj=BytesIO(archive)) as files:
        files.extractall(path, filter="data")


def app(compose, service, code):
    result = run(compose + ["exec", "-T", service, "python", "manage.py", "shell", "--verbosity", "0"],
                 input=code, encoding="utf-8", stdout=subprocess.PIPE)
    return json.loads(result.stdout.strip().splitlines()[-1])


def original_fields(database, columns=None):
    """Compara todas las columnas originales de aplicación aunque se agreguen otras."""
    result = {}
    for schema, table in database.tables():
        if table in {"django_migrations", "django_content_type", "auth_permission"}:
            continue
        name = identifier(schema) + "." + identifier(table)
        if columns is not None and name not in columns:
            continue
        if columns is None:
            relation = name.replace("'", "''")
            names = database.sql("SELECT attname FROM pg_attribute WHERE attrelid='" + relation + "'::regclass AND attnum>0 AND NOT attisdropped ORDER BY attnum")
        else:
            names = columns[name]["columns"]
        select = ",".join(identifier(item) for item in names)
        rows = database.iter_sql("SET extra_float_digits=3; SELECT row_to_json(t)::text FROM (SELECT " + select + " FROM " + name + ") t")
        hashes = sorted(hashlib.sha256(json.dumps(json.loads(row), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).digest() for row in rows)
        total = hashlib.sha256()
        for digest in hashes:
            total.update(digest)
        result[name] = {"columns": names, "count": len(hashes), "sha256": total.hexdigest()}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--keep-running", action="store_true")
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()
    if not args.project.startswith("lizardjudge-upgrade-"):
        parser.error("Use un nombre nuevo con prefijo lizardjudge-upgrade-.")
    os.environ["POSTGRES_PASSWORD"] = secrets.token_urlsafe(32)
    os.environ["JUDGE_SERVER_TOKEN"] = secrets.token_urlsafe(32)
    compose_file = str(ROOT / "compose.upgrade-verify.yml")
    compose = ["docker", "compose", "-p", args.project, "-f", compose_file]
    existing = subprocess.check_output(["docker", "ps", "-aq", "--filter", "label=com.docker.compose.project=" + args.project], text=True).strip()
    if existing:
        raise ValueError("El proyecto ya existe. Use otro nombre; se conservan sus datos.")
    export_legacy()
    frontend = subprocess.check_output(["git", "-c", "safe.directory=" + str(ROOT / "OnlineJudgeFE"), "-C", str(ROOT / "OnlineJudgeFE"), "rev-parse", "HEAD"], text=True).strip()
    if not args.skip_build:
        backend_sha = subprocess.check_output(["git", "-C", str(ROOT / "OnlineJudge"), "rev-parse", "HEAD"], text=True).strip()
        root_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        common = ["docker", "build", "--build-arg", "FRONTEND_COMMIT=" + frontend, "--build-arg", "INTEGRATION_COMMIT=" + root_sha]
        run(common + ["--build-arg", "BACKEND_COMMIT=" + backend_sha, "-t", "lizardjudge-sprints:local", "."])
        run(common + ["--build-arg", "BACKEND_COMMIT=" + LEGACY, "--build-arg", "BACKEND_SOURCE=.verification/legacy-backend", "-t", "lizardjudge-legacy:verification", "."])
    directory = ROOT / "respaldos" / args.project
    dbargs = ["--project", args.project, "--compose-file", compose_file, "--directory", str(directory), "--writers-stopped"]
    source, target = Database(compose, "oj-postgres"), Database(compose, "oj-postgres17")
    success = False
    try:
        run(compose + ["up", "-d", "--wait", "oj-postgres", "oj-postgres17", "oj-redis"])
        if source.tables() or target.tables():
            raise ValueError("El ensayo requiere bases nuevas; se conservan los volúmenes existentes.")
        run(compose + ["up", "-d", "--wait", "--wait-timeout", "150", "oj-legacy"])
        seed = '''
import os, json, secrets, hashlib
from pathlib import Path
assert os.environ.get("OJ_VERIFICATION_ONLY") == "1"
from account.models import User, UserProfile, AdminType, ProblemPermission
from problem.tests import DEFAULT_PROBLEM_DATA, ProblemCreateTestBase
from contest.tests import DEFAULT_CONTEST_DATA
from contest.models import Contest
from submission.models import Submission
from ai_tutor.models import TutorSession, TutorAttempt
from ai_tutor.tests.config_factory import create_active_config
from django.contrib.sessions.backends.cache import SessionStore
from django.core.cache import cache
from django.db import connection
assert User.objects.count() == 1
user = User(username="ensayo-historico", admin_type=AdminType.SUPER_ADMIN, problem_permission=ProblemPermission.ALL)
user.set_password(secrets.token_urlsafe(32)); user.save()
UserProfile.objects.create(user=user, language="es-LA")
problem = ProblemCreateTestBase.add_problem(dict(DEFAULT_PROBLEM_DATA, _id="UPGRADE-1"), user)
version = create_active_config(problem, user)
session = TutorSession.objects.create(user=user, problem=problem, config_version=version)
submission = Submission.objects.create(user_id=user.id, username=user.username, problem=problem, code="print(2)\\n", language="Python3", result=0)
TutorAttempt.objects.create(session=session, submission=submission, language=submission.language, result=0)
contest = Contest.objects.create(created_by=user, **DEFAULT_CONTEST_DATA)
contest_problem = ProblemCreateTestBase.add_problem(dict(DEFAULT_PROBLEM_DATA, _id="UPGRADE-C", contest=contest), user)
Submission.objects.create(user_id=user.id, username=user.username, problem=contest_problem, contest=contest, code="print(2)", language="Python3", result=0)
store = SessionStore(); store["_auth_user_id"] = str(user.id); store["_auth_user_backend"] = "django.contrib.auth.backends.ModelBackend"; store["_auth_user_hash"] = user.get_session_auth_hash(); store.save()
user.session_keys = [store.session_key]; user.save()
cache.set("upgrade-session-id", store.session_key)
Path("/data/public/upload/conservacion.txt").write_text("Archivo de ensayo.\\n", encoding="utf-8")
with connection.cursor() as cursor:
    cursor.execute("SELECT lo_from_bytea(0, %s)", [b"objeto-grande-publico-de-ensayo"])
print(json.dumps({"user_id": user.id, "key_sha256": hashlib.sha256(Path("/data/config/secret.key").read_bytes()).hexdigest()}))
'''
        before = app(compose, "oj-legacy", seed)
        run(compose + ["stop", "oj-legacy"])
        originals = original_fields(source)
        run([sys.executable, "backup/database.py", "backup"] + dbargs)
        container = subprocess.check_output(compose + ["ps", "-a", "-q", "oj-legacy"], text=True).strip()
        run([sys.executable, "backup/files_backup.py", "--container", container, "--output", str(directory / "backend-data.tar.gz")])
        run([sys.executable, "backup/database.py", "restore"] + dbargs)
        duplicate = subprocess.run([sys.executable, "backup/database.py", "restore"] + dbargs, cwd=ROOT)
        assert duplicate.returncode != 0, "Se permitió sobrescribir un destino poblado."
        dump = directory / "database.dump"
        length = dump.stat().st_size
        with dump.open("ab") as stream:
            stream.write(b"alteracion-sintetica")
        try:
            invalid = subprocess.run([sys.executable, "backup/database.py", "verify"] + dbargs, cwd=ROOT)
            assert invalid.returncode != 0, "Se aceptó un respaldo alterado."
        finally:
            with dump.open("r+b") as stream:
                stream.truncate(length)
        assert original_fields(target, originals) == originals, "Cambió una columna de aplicación durante la restauración."
        # Ensayo de reversión previo a abrir escrituras: la aplicación anterior sigue saludable sobre 10.
        run(compose + ["up", "-d", "--wait", "--wait-timeout", "120", "oj-legacy"])
        rollback = app(compose, "oj-legacy", 'from account.models import User; import json; print(json.dumps({"users": User.objects.count()}))')
        assert rollback["users"] == 2
        run(compose + ["stop", "oj-legacy"])
        assert original_fields(source) == originals, "El ensayo alteró el origen."
        # Redis se restaura en otro volumen: conservar la clave Django por sí sola
        # no demuestra que las sesiones cacheadas sobrevivan una recuperación.
        run(compose + ["exec", "-T", "oj-redis", "redis-cli", "SAVE"])
        redis_source = subprocess.check_output(compose + ["ps", "-q", "oj-redis"], text=True).strip()
        redis_dump = directory / "redis.rdb"
        run(["docker", "cp", redis_source + ":/data/dump.rdb", str(redis_dump)])
        os.chmod(redis_dump, 0o600)
        redis_digest = hashlib.sha256(redis_dump.read_bytes()).hexdigest()
        run(compose + ["create", "oj-redis-restore"])
        redis_target = subprocess.check_output(compose + ["ps", "-a", "-q", "oj-redis-restore"], text=True).strip()
        run(["docker", "cp", str(redis_dump), redis_target + ":/data/dump.rdb"])
        run(compose + ["up", "-d", "--wait", "oj-redis-restore"])
        run(compose + ["create", "oj-backend"])
        backend_target = subprocess.check_output(compose + ["ps", "-a", "-q", "oj-backend"], text=True).strip()
        target_info = json.loads(subprocess.check_output(["docker", "inspect", backend_target], text=True))[0]
        target_volume = next(mount["Name"] for mount in target_info["Mounts"] if mount["Destination"] == "/data")
        run([sys.executable, "backup/files_restore.py", "--source-container", container, "--target-volume", target_volume,
             "--archive", str(directory / "backend-data.tar.gz")])
        run(compose + ["up", "-d", "--wait", "--wait-timeout", "150", "oj-backend"])
        assert original_fields(target, originals) == originals, "Las migraciones modificaron datos originales."
        after = app(compose, "oj-backend", '''
import json, hashlib
from pathlib import Path
from django.core.cache import cache
from django.test import Client
from practice.models import Achievement
from account.models import User
key = cache.get("upgrade-session-id"); assert key
client = Client(); client.cookies["sessionid"] = key
response = client.get("/api/profile")
assert response.status_code == 200 and response.data["data"]["user"]["username"] == "ensayo-historico"
assert User.objects.count() == 2 and Achievement.objects.count() == 1
assert Path("/data/public/upload/conservacion.txt").read_text(encoding="utf-8") == "Archivo de ensayo.\\n"
print(json.dumps({"key_sha256": hashlib.sha256(Path("/data/config/secret.key").read_bytes()).hexdigest(), "achievements": Achievement.objects.count()}))
''')
        assert before["key_sha256"] == after["key_sha256"]
        run(compose + ["exec", "-T", "oj-backend", "python", "manage.py", "check"])
        run(compose + ["exec", "-T", "oj-backend", "python", "manage.py", "makemigrations", "--check", "--dry-run"])
        run(compose + ["exec", "-T", "oj-backend", "python", "manage.py", "test", "--settings=oj.test_settings", "--noinput", "--verbosity", "0"])
        report = {"legacy_backend": LEGACY, "application_tables_checked": len(originals), "original_columns_preserved": True,
                  "key_preserved": True, "legacy_session_preserved": True, "historical_achievement_count": after["achievements"],
                  "redis_restored_on_new_volume": True, "redis_backup_sha256": redis_digest,
                  "files_restored_on_new_volume": True,
                  "rollback_before_writes": "passed", "production_access": False}
        (directory / "upgrade-result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("OK: actualización con datos, clave, sesión y archivos conservados; reconciliación histórica y reversión verificadas.")
        success = True
    finally:
        if not (args.keep_running and success):
            run(compose + ["stop"])


if __name__ == "__main__":
    main()
