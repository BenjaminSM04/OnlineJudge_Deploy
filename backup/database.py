"""Respaldo y restauración lógica sin sobrescribir una base existente."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def identifier(value):
    return '"' + value.replace('"', '""') + '"'


class Database:
    def __init__(self, compose, service):
        self.compose = compose
        self.service = service

    def command(self, command):
        return self.compose + ["exec", "-T", self.service, "sh", "-eu", "-c", command]

    def sql(self, sql):
        return list(self.iter_sql(sql))

    def iter_sql(self, sql):
        command = 'exec psql -X -qAt -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
        with subprocess.Popen(self.command(command), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL) as process:
            process.stdin.write(sql.encode())
            process.stdin.close()
            for row in process.stdout:
                yield row.decode().rstrip("\r\n")
            if process.wait() != 0:
                raise ValueError("Falló una consulta de verificación; no abra escrituras.")

    def tables(self):
        return [json.loads(row) for row in self.sql("""
            SELECT json_build_array(schemaname, tablename) FROM pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
              AND schemaname NOT LIKE 'pg_toast%' ORDER BY schemaname, tablename;
        """)]

    def fingerprint(self):
        # Solo se conservan hashes de filas; nunca se escriben sus contenidos.
        tables = {}
        for schema, table in self.tables():
            name = identifier(schema) + "." + identifier(table)
            rows = self.iter_sql("SET extra_float_digits=3; SELECT row_to_json(t)::text FROM " + name + " t;")
            hashes = sorted(hashlib.sha256(json.dumps(json.loads(row), sort_keys=True,
                            separators=(",", ":"), ensure_ascii=True).encode()).digest() for row in rows)
            table_hash = hashlib.sha256()
            for row_hash in hashes:
                table_hash.update(row_hash)
            tables[name] = {"rows": len(hashes), "sha256": table_hash.hexdigest()}
        sequences = {}
        for row in self.sql("""
            SELECT json_build_array(sequence_schema, sequence_name) FROM information_schema.sequences
            WHERE sequence_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY sequence_schema, sequence_name;
        """):
            schema, sequence = json.loads(row)
            name = identifier(schema) + "." + identifier(sequence)
            sequences[name] = self.sql("SELECT last_value::text || ':' || is_called::text FROM " + name)[0]
        large_objects = self.sql("SELECT loid || ':' || pageno || ':' || md5(data) FROM pg_largeobject ORDER BY loid, pageno")
        return {"tables": tables, "sequences": sequences,
                "large_objects_sha256": hashlib.sha256("\n".join(large_objects).encode()).hexdigest()}

    def mounts(self):
        container = subprocess.check_output(self.compose + ["ps", "-q", self.service], text=True).strip()
        if not container:
            raise ValueError("El servicio de base de datos debe estar iniciado.")
        info = json.loads(subprocess.check_output(["docker", "inspect", container], text=True))[0]
        return {mount["Source"] for mount in info["Mounts"]}


def offline(compose, databases):
    running = subprocess.check_output(compose + ["ps", "--status", "running", "--services"], text=True).splitlines()
    if set(running) - set(databases) - {"oj-redis"}:
        raise ValueError("Detenga backend, juez y trabajadores del proyecto antes de continuar.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["backup", "restore", "verify"])
    parser.add_argument("--project", required=True, help="Nombre real del proyecto Compose; no se infiere.")
    parser.add_argument("--compose-file", action="append", required=True)
    parser.add_argument("--source", default="oj-postgres")
    parser.add_argument("--target", default="oj-postgres17")
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--writers-stopped", action="store_true", help="Confirma también el cierre de escritores externos.")
    args = parser.parse_args()
    if not args.writers_stopped:
        parser.error("Cierre las escrituras, drene el juez y use --writers-stopped.")
    if args.source == args.target:
        parser.error("Origen y destino deben ser servicios diferentes.")
    compose = ["docker", "compose", "-p", args.project]
    for file in args.compose_file:
        compose += ["-f", file]
    source, target = Database(compose, args.source), Database(compose, args.target)
    offline(compose, [args.source, args.target])
    dump = args.directory / "database.dump"
    manifest = args.directory / "manifest.json"
    if args.action == "backup":
        args.directory.mkdir(mode=0o700, parents=True, exist_ok=False)
        with dump.open("xb") as stream:
            os.chmod(dump, 0o600)
            subprocess.run(source.command('exec pg_dump -Fc --no-owner --no-acl -U "$POSTGRES_USER" "$POSTGRES_DB"'),
                           stdout=stream, stderr=subprocess.DEVNULL, check=True)
        # Un archivo incompleto no recibe manifiesto y nunca puede restaurarse.
        with dump.open("rb") as stream:
            subprocess.run(source.command("exec pg_restore --list"), stdin=stream,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        metadata = {"format": 1, "dump_sha256": digest(dump), "source": source.fingerprint()}
        with manifest.open("x", encoding="utf-8") as stream:
            os.chmod(manifest, 0o600)
            json.dump(metadata, stream, indent=2, ensure_ascii=True)
        print("Respaldo validado; conserve el directorio protegido fuera de Git.")
        return
    metadata = json.loads(manifest.read_text(encoding="utf-8"))
    if metadata["format"] != 1 or metadata["dump_sha256"] != digest(dump):
        raise ValueError("Formato desconocido o respaldo alterado: operación rechazada.")
    if args.action == "restore":
        if source.mounts() & target.mounts():
            raise ValueError("Origen y destino comparten almacenamiento: operación rechazada.")
        if int(target.sql("SHOW server_version_num")[0]) // 10000 != 17:
            raise ValueError("El destino de esta transición debe ser PostgreSQL 17.")
        if target.tables() or target.sql("SELECT 1 FROM pg_largeobject_metadata LIMIT 1") or target.sql(
                "SELECT 1 FROM information_schema.sequences LIMIT 1"):
            raise ValueError("El destino contiene datos: no se sobrescribe.")
        with dump.open("rb") as stream:
            contents = subprocess.check_output(target.command("exec pg_restore --list"), stdin=stream,
                                               stderr=subprocess.DEVNULL)
        # Los dumps antiguos incluyen CREATE SCHEMA public. Conservar el esquema
        # vacío de initdb sin ejecutar DROP SCHEMA ni omitir otros esquemas.
        contents = b"\n".join(row for row in contents.splitlines() if b" SCHEMA - public " not in row) + b"\n"
        restore_list = "/tmp/restore-" + uuid.uuid4().hex + ".list"
        try:
            subprocess.run(target.command("umask 077; cat > " + restore_list), input=contents, check=True)
            with dump.open("rb") as stream:
                subprocess.run(target.command('exec pg_restore --single-transaction --exit-on-error --no-owner --no-acl '
                                              '--use-list ' + restore_list + ' -U "$POSTGRES_USER" -d "$POSTGRES_DB"'), stdin=stream,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        finally:
            subprocess.run(target.command("rm -f " + restore_list), check=True)
    if target.fingerprint() != metadata["source"]:
        raise ValueError("La comparación de tablas, filas, secuencias u objetos grandes falló. No abra escrituras.")
    print("Restauración comprobada: coinciden filas, hashes, secuencias y objetos grandes.")
    print("No se ha cambiado la conexión de la aplicación ni abierto las escrituras.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        # No imprimir stderr de PostgreSQL: puede incluir valores privados.
        print("Operación detenida: " + (str(error) if isinstance(error, ValueError) else type(error).__name__), file=sys.stderr)
        sys.exit(1)
