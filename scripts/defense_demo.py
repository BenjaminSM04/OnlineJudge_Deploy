"""Ciclo de vida de la defensa local: solo volúmenes propios, sin datos reales."""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run(command, **kwargs):
    return subprocess.run(command, cwd=ROOT, check=True, **kwargs)


def revision(path):
    dirty = subprocess.check_output(["git", "-C", str(path), "status", "--porcelain"], text=True).strip()
    head = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    return "working-tree-" + head[:12] if dirty else head


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("init", "start", "stop", "status"))
    parser.add_argument("--project", default="lizardjudge-defensa-20261024")
    parser.add_argument("--port", type=int, default=18084)
    parser.add_argument("--model-directory", type=Path)
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"lizardjudge-defensa-[a-z0-9][a-z0-9-]{0,40}", args.project) or not 1024 <= args.port <= 65535:
        parser.error("Proyecto de defensa o puerto no válido.")
    private = ROOT / ".verification/runtime/defensa" / args.project
    state_file = private / "state.json"
    env_file = private / "private.env"
    if args.action == "init":
        if private.exists():
            parser.error("La demostración ya tiene estado; use start para conservarla o elija otro proyecto.")
        for kind, command in (("contenedores", ["docker", "ps", "-aq"]), ("volúmenes", ["docker", "volume", "ls", "-q"])):
            existing = subprocess.check_output(command + ["--filter", "label=com.docker.compose.project=" + args.project], text=True).strip()
            if existing:
                parser.error("Ya existen " + kind + " con ese nombre; se conservan. Elija otro proyecto.")
        volumes = set(subprocess.check_output(["docker", "volume", "ls", "--format", "{{.Name}}"], text=True).splitlines())
        if volumes & {args.project+"_"+suffix for suffix in ("postgres", "redis", "backend")}:
            parser.error("Ya existe un volumen de destino, incluso sin etiquetas; se conserva. Elija otro proyecto.")
        model = args.model_directory.resolve() if args.model_directory else None
        if model:
            manifest = json.loads((model / "manifest.json").read_text(encoding="utf-8"))
            if manifest.get("scope") != "technical-demo" or manifest.get("decision") != "demonstration":
                parser.error("Este perfil admite únicamente el artefacto experimental explícito.")
        state = {"project": args.project, "port": args.port, "model_enabled": bool(model), "initialized": False,
                 "teacher_password": secrets.token_urlsafe(18), "student_password": secrets.token_urlsafe(18)}
        private.mkdir(parents=True)
        os.chmod(private, 0o700)
        environment = {"POSTGRES_PASSWORD": secrets.token_urlsafe(32), "JUDGE_SERVER_TOKEN": secrets.token_urlsafe(32),
                       "DEFENSE_PORT": str(args.port), "DEFENSE_MODEL_ENABLED": "1" if model else "0",
                       "DEFENSE_MODEL_DIRECTORY": model.as_posix() if model else "./artifacts/no-model"}
        with env_file.open("x", encoding="utf-8") as stream:
            stream.write("\n".join(key+"="+json.dumps(value) for key,value in environment.items())+"\n")
        os.chmod(env_file, 0o600)
        with state_file.open("x", encoding="utf-8") as stream:
            json.dump(state, stream, indent=2)
        os.chmod(state_file, 0o600)
    else:
        state = json.loads(state_file.read_text(encoding="utf-8"))
        if state["project"] != args.project:
            parser.error("El estado no corresponde al proyecto solicitado.")
    compose = ["docker", "compose", "--env-file", str(env_file), "-p", args.project, "-f", str(ROOT / "compose.defensa.yml")]
    if state["model_enabled"]:
        compose += ["--profile", "model"]
    if args.action in ("init", "start"):
        if args.build:
            run(["docker", "build", "--build-arg", "INTEGRATION_COMMIT="+revision(ROOT),
                 "--build-arg", "BACKEND_COMMIT="+revision(ROOT/"OnlineJudge"), "--build-arg", "FRONTEND_COMMIT="+revision(ROOT/"OnlineJudgeFE"),
                 "-t", "lizardjudge-defensa:local", "."])
            run(["docker", "build", "--build-arg", "INTEGRATION_COMMIT="+revision(ROOT), "-f", "tutor_engine/Dockerfile", "-t", "lizardjudge-tutor:local", "."])
        run(compose + ["up", "-d", "--wait", "--wait-timeout", "240"])
        if not state["initialized"]:
            credentials = {key: state[key] for key in ("teacher_password", "student_password")}
            run(compose + ["exec", "-T", "oj-backend", "python", "manage.py", "seed_defense_demo"], input=json.dumps(credentials), encoding="utf-8")
            state["initialized"] = True
            state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        print("Demostración:", "http://127.0.0.1:"+str(state["port"]))
        print("Cuentas ficticias: docente-demo / estudiante-demo. Contraseñas en archivo privado:", state_file)
    elif args.action == "stop":
        run(compose + ["stop"])
        print("Contenedores detenidos; volúmenes, claves y archivos conservados.")
    else:
        run(compose + ["ps"])


if __name__ == "__main__":
    main()
