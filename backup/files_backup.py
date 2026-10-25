"""Copia protegida de /data desde los montajes reales de un backend detenido."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--container", required=True, help="Contenedor exacto del backend detenido.")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    info = json.loads(subprocess.check_output(["docker", "inspect", args.container], text=True))[0]
    if info["State"]["Running"]:
        parser.error("Detenga backend y trabajadores antes de respaldar los archivos.")
    if not any(mount["Destination"] == "/data" for mount in info["Mounts"]):
        parser.error("El contenedor no tiene un montaje /data; compruebe los volúmenes reales.")
    # volumes-from conserva también los montajes anidados; todos quedan de solo lectura.
    with args.output.open("xb") as stream:
        os.chmod(args.output, 0o600)
        subprocess.run(["docker", "run", "--rm", "--network", "none", "--volumes-from", args.container + ":ro",
                        "--entrypoint", "tar", info["Image"], "-czf", "-", "-C", "/data", "."],
                       stdout=stream, check=True)
    sha = hashlib.sha256()
    with args.output.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    manifest = args.output.with_suffix(args.output.suffix + ".sha256")
    with manifest.open("x", encoding="utf-8") as stream:
        os.chmod(manifest, 0o600)
        stream.write(sha.hexdigest() + "  " + args.output.name + "\n")
    print("Archivos respaldados. Incluye claves y casos privados: conserve la copia fuera de Git.")


if __name__ == "__main__":
    main()
