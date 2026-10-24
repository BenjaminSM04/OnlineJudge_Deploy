"""Restaura /data únicamente en un volumen Docker existente, separado y vacío."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-container", required=True)
    parser.add_argument("--target-volume", required=True)
    parser.add_argument("--archive", required=True, type=Path)
    args = parser.parse_args()
    info = json.loads(subprocess.check_output(["docker", "inspect", args.source_container], text=True))[0]
    if info["State"]["Running"]:
        parser.error("El backend de origen debe estar detenido.")
    target = json.loads(subprocess.check_output(["docker", "volume", "inspect", args.target_volume], text=True))[0]
    sources = [mount for mount in info["Mounts"] if mount["Destination"] == "/data" or mount["Destination"].startswith("/data/")]
    if not sources or any(mount.get("Name") == target["Name"] or mount["Source"] == target["Mountpoint"] for mount in sources):
        parser.error("El destino debe estar separado de todos los montajes de datos originales.")
    expected = args.archive.with_suffix(args.archive.suffix + ".sha256").read_text().split()[0]
    digest = hashlib.sha256()
    with args.archive.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected:
        parser.error("El respaldo de archivos fue alterado.")
    code = '''
import hashlib,json,pathlib,sys,tarfile
root=pathlib.Path('/restore')
if any(root.iterdir()): raise ValueError('El destino no está vacío; no se sobrescribe.')
count=0
with tarfile.open(fileobj=sys.stdin.buffer,mode='r|gz') as archive:
    for member in archive:
        if member.issym() or member.islnk() or member.isdev() or member.isfifo():
            raise ValueError('Tipo de archivo no admitido; revise el respaldo sin abrir escrituras.')
        archive.extract(member,root,filter='data')
        if member.isfile(): count+=1
print(json.dumps({'restored_files':count,'overwritten':False}))
'''
    with args.archive.open("rb") as stream:
        subprocess.run(["docker", "run", "--rm", "-i", "--network", "none", "--read-only",
                        "--mount", "type=volume,source=" + target["Name"] + ",target=/restore",
                        "--entrypoint", "python3", info["Image"], "-c", code], stdin=stream, check=True)


if __name__ == "__main__":
    main()
