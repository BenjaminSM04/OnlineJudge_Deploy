"""Medición preliminar de latencia y memoria de modelos GGUF candidatos sobre borradores sintéticos no aprobados; no selecciona ni aprueba nada."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import socket
import statistics
import subprocess
import tempfile
import threading
import time
import urllib.request
import uuid
from datetime import datetime, timezone

RAIZ = Path(__file__).resolve().parent.parent
BORRADORES = RAIZ / "OnlineJudge" / "docs" / "ai-tutor" / "variantes" / "ejemplos-borrador.json"
GUARD = RAIZ / "OnlineJudge" / "ai_tutor" / "services" / "output_guard.py"
IMAGEN_CPU = "ghcr.io/ggml-org/llama.cpp:server@sha256:8c74db29f1a2bef3f0a331b52c4d6214601dfceed4bee0b94cc48b3b23ff257d"
IMAGEN_GPU = "ghcr.io/ggml-org/llama.cpp:server-cuda"
MOTOR = RAIZ / "tutor_engine" / "server.py"
SISTEMA = "Orienta sin dar una solución completa. Devuelve JSON con content y uncertainty."
CAMPOS = ("problem", "language", "faulty_code", "verdict", "concept")
# Presupuesto por defecto de MODEL_TIMEOUT_S en tutor_engine/server.py. Hasta cf7174e el motor
# cortaba a 0.5 s porque el timeout de socket regía también la espera de la generación.
PRESUPUESTO_MOTOR_MS = 8000
PLAZO_ANTERIOR_MS = 500
SEGURIDAD = ["--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true", "--pids-limit", "64", "--tmpfs", "/tmp:size=64m"]
LIMITES = {
    "cpu": {"cpus": "2", "memoria": "3g", "hilos": 2, "contexto": 4096, "ranuras": 1},
    "gpu": {"cpus": None, "memoria": "6g", "capas_gpu": 99, "contexto": 4096, "ranuras": 1},
}
UNIDADES_MIB = {"B": 1 / 1048576, "KB": 1 / 1024, "KIB": 1 / 1024, "MB": 1000000 / 1048576, "MIB": 1.0, "GB": 1000000000 / 1048576, "GIB": 1024.0}
ESPERA_LISTO_S = 300
TIMEOUT_PETICION_S = 120


def cargar_guard():
    # Igual que el Dockerfile del motor: el módulo se carga por ruta, sin depender de Django.
    spec = importlib.util.spec_from_file_location("guard", GUARD)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo.validate_output


def sha256_archivo(ruta):
    resumen = hashlib.sha256()
    with ruta.open("rb") as flujo:
        for bloque in iter(lambda: flujo.read(1024 * 1024), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def ejecutar(comando, **kwargs):
    return subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=kwargs.pop("timeout", 15), **kwargs)


def nombre_gpu():
    try:
        salida = ejecutar(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"])
        return salida.stdout.strip().splitlines()[0] if salida.returncode == 0 and salida.stdout.strip() else None
    except Exception:
        return None


def vram_usada_mib():
    try:
        salida = ejecutar(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"])
        return float(salida.stdout.strip().splitlines()[0])
    except Exception:
        return None


def ram_contenedor_mib(nombre):
    try:
        salida = ejecutar(["docker", "stats", "--no-stream", "--format", "{{.MemUsage}}", nombre])
        valor, unidad = re.match(r"\s*([\d.]+)\s*([A-Za-z]+)", salida.stdout).groups()
        return float(valor) * UNIDADES_MIB[unidad.upper()]
    except Exception:
        return None


class Muestreador(threading.Thread):
    """Toma muestras de RAM (y VRAM en gpu) cada 0.5 s mientras se atienden las peticiones."""

    def __init__(self, nombre, con_gpu):
        super().__init__(daemon=True)
        self.nombre, self.con_gpu = nombre, con_gpu
        self.parar = threading.Event()
        self.ram, self.vram = [], []

    def run(self):
        while not self.parar.is_set():
            valor = ram_contenedor_mib(self.nombre)
            if valor is not None:
                self.ram.append(valor)
            if self.con_gpu:
                vram = vram_usada_mib()
                if vram is not None:
                    self.vram.append(vram)
            self.parar.wait(0.5)


def puerto_libre():
    with socket.socket() as zocalo:
        zocalo.bind(("127.0.0.1", 0))
        return zocalo.getsockname()[1]


def asegurar_imagen(imagen):
    # La descarga queda fuera del tiempo de carga del modelo.
    if subprocess.run(["docker", "image", "inspect", imagen], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
        print("Descargando imagen " + imagen, flush=True)
        subprocess.run(["docker", "pull", imagen], check=True)
    return ejecutar(["docker", "image", "inspect", "-f", "{{.Id}}", imagen]).stdout.strip()


def comando_docker(modo, imagen, nombre, puerto, modelo):
    recursos = ["--cpus", "2", "--memory", "3g"] if modo == "cpu" else ["--gpus", "all", "--memory", "6g"]
    servidor = ["-m", "/models/model.gguf", "--host", "0.0.0.0", "--port", "8080", "-c", "4096", "-np", "1"]
    servidor += ["--threads", "2"] if modo == "cpu" else ["-ngl", "99"]
    return (["docker", "run", "--rm", "--name", nombre, "-p", "127.0.0.1:%d:8080" % puerto, "--mount",
             "type=bind,source=%s,target=/models/model.gguf,readonly" % modelo] + recursos + SEGURIDAD + [imagen] + servidor)


def detener(nombre, proceso):
    subprocess.run(["docker", "stop", "-t", "5", nombre], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        proceso.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proceso.kill()


def esperar_listo(puerto, proceso, registro):
    inicio = time.monotonic()
    while time.monotonic() - inicio < ESPERA_LISTO_S:
        if proceso.poll() is not None:
            registro.seek(0)
            cola = registro.read().decode("utf-8", "replace").strip().splitlines()[-5:]
            raise RuntimeError("El contenedor terminó antes de estar listo: " + " | ".join(cola)[:400])
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/health" % puerto, timeout=2) as respuesta:
                if respuesta.status == 200:
                    return time.monotonic() - inicio
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError("Sin readiness tras %d s." % ESPERA_LISTO_S)


def percentil(valores, p):
    return valores[max(0, (len(valores) * p + 99) // 100 - 1)] if valores else None


def evaluar_contenido(contenido, revision, validar):
    """Devuelve (json_valido, veredicto del guard) con la misma preparación que el motor."""
    try:
        generado = json.loads(contenido)
    except (TypeError, ValueError):
        return False, "no-evaluable"
    if not isinstance(generado, dict) or not {"content", "uncertainty"} <= set(generado):
        return False, "no-evaluable"
    generado["model_version"] = revision
    try:
        validar(generado)
    except ValueError as error:
        return True, "rechazado:" + str(error)
    return True, "aceptado"


def prompt_motor():
    """Mensaje de sistema leído del propio motor para no divergir de producción."""
    spec = importlib.util.spec_from_file_location("tutor_prompt", RAIZ / "OnlineJudge/ai_tutor/ml/prompt.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SYSTEM_PROMPT


def carga_peticion(item, peticion, sistema_motor):
    if peticion == "benchmark":
        return {"messages": [{"role": "system", "content": SISTEMA},
                             {"role": "user", "content": json.dumps({clave: item[clave] for clave in CAMPOS}, ensure_ascii=True)}],
                "max_tokens": 400, "temperature": 0, "seed": 2026}
    # Misma forma que el contexto validado por el motor; sin clasificador entrenado se envía una categoría neutra.
    contexto = {"schema_version": "1.0", "action": "hint", "level": 1, "concept": item["concept"], "problem": item["problem"],
                "code": item["faulty_code"], "language": item["language"], "diagnostic": {"verdict": item["verdict"], "evidence": ""},
                "concepts": [], "history": [], "config_version": 1}
    return {"messages": [{"role": "system", "content": sistema_motor},
                         {"role": "user", "content": json.dumps({"context": contexto, "classification": {"category": "desconocida", "confidence": 0.0}}, ensure_ascii=True)}],
            "max_tokens": 400, "temperature": 0, "seed": 2026, "response_format": {"type": "json_object"}}


def preguntar(puerto, carga):
    peticion = urllib.request.Request("http://127.0.0.1:%d/v1/chat/completions" % puerto, json.dumps(carga).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(peticion, timeout=TIMEOUT_PETICION_S) as respuesta:
        crudo = respuesta.read(1000001)
    if len(crudo) > 1000000:
        raise ValueError("tamaño")
    return json.loads(crudo)


def medir_candidato(candidato, modo, imagen, ejemplos, validar, peticion, sistema_motor):
    meta = {clave: valor for clave, valor in candidato.items() if clave != "path"}
    nombre = "lizardjudge-medicion-" + uuid.uuid4().hex[:10]
    puerto = puerto_libre()
    vram_basal = vram_usada_mib() if modo == "gpu" else None
    comando = comando_docker(modo, imagen, nombre, puerto, candidato["path"])
    resultado = {"candidato": meta, "tiempo_carga_s": None, "latencia_p50_ms": None, "latencia_p95_ms": None, "latencia_max_ms": None,
                 "errores": 0, "json_valido": 0, "guard_rechazos": 0, "guard_no_evaluables": 0, "tokens_por_segundo_p50": None,
                 "ram_pico_mib": None, "vram_basal_mib": vram_basal, "vram_pico_mib": None,
                 "dentro_plazo_anterior": 0, "dentro_presupuesto_motor": 0, "utiles_en_motor": 0, "respuestas": []}
    with tempfile.TemporaryFile() as registro:
        proceso = subprocess.Popen(comando, stdout=registro, stderr=subprocess.STDOUT)
        muestreador = None
        try:
            resultado["tiempo_carga_s"] = round(esperar_listo(puerto, proceso, registro), 2)
            muestreador = Muestreador(nombre, modo == "gpu")
            muestreador.start()
            latencias, velocidades = [], []
            for item in ejemplos:
                fila = {"example_id": item["example_id"], "estado": "failed", "latencia_ms": None, "tokens_generados": None,
                        "tokens_por_segundo": None, "json_valido": False, "veredicto_guard": "no-evaluable", "muestra_respuesta": ""}
                inicio = time.monotonic()
                try:
                    datos = preguntar(puerto, carga_peticion(item, peticion, sistema_motor))
                    transcurrido = time.monotonic() - inicio
                    contenido = datos["choices"][0]["message"]["content"]
                    fila["estado"] = "completed"
                    fila["muestra_respuesta"] = contenido[:300]
                    tiempos = datos.get("timings") or {}
                    fila["tokens_generados"] = tiempos.get("predicted_n", (datos.get("usage") or {}).get("completion_tokens"))
                    if tiempos.get("predicted_per_second"):
                        fila["tokens_por_segundo"] = round(tiempos["predicted_per_second"], 2)
                    elif fila["tokens_generados"] and transcurrido > 0:
                        # Incluye el procesamiento del prompt: es una cota inferior.
                        fila["tokens_por_segundo"] = round(fila["tokens_generados"] / transcurrido, 2)
                    fila["json_valido"], fila["veredicto_guard"] = evaluar_contenido(contenido, candidato["revision"], validar)
                except Exception as error:
                    transcurrido = time.monotonic() - inicio
                    fila["error"] = type(error).__name__
                fila["latencia_ms"] = round(transcurrido * 1000)
                resultado["respuestas"].append(fila)
                if fila["estado"] == "completed":
                    latencias.append(fila["latencia_ms"])
                    if fila["tokens_por_segundo"]:
                        velocidades.append(fila["tokens_por_segundo"])
                else:
                    resultado["errores"] += 1
                resultado["json_valido"] += fila["json_valido"]
                resultado["guard_rechazos"] += fila["veredicto_guard"].startswith("rechazado")
                resultado["guard_no_evaluables"] += fila["estado"] == "completed" and fila["veredicto_guard"] == "no-evaluable"
                completada = fila["estado"] == "completed"
                resultado["dentro_plazo_anterior"] += completada and fila["latencia_ms"] <= PLAZO_ANTERIOR_MS
                resultado["dentro_presupuesto_motor"] += completada and fila["latencia_ms"] <= PRESUPUESTO_MOTOR_MS
                resultado["utiles_en_motor"] += (completada and fila["latencia_ms"] <= PRESUPUESTO_MOTOR_MS
                                                 and fila["veredicto_guard"] == "aceptado")
            valores = sorted(latencias)
            if valores:
                resultado.update(latencia_p50_ms=statistics.median(valores), latencia_p95_ms=percentil(valores, 95), latencia_max_ms=valores[-1])
            if velocidades:
                resultado["tokens_por_segundo_p50"] = round(statistics.median(velocidades), 2)
        except RuntimeError as error:
            resultado["error_arranque"] = str(error)
        finally:
            if muestreador:
                muestreador.parar.set()
                muestreador.join(timeout=20)
                if muestreador.ram:
                    resultado["ram_pico_mib"] = round(max(muestreador.ram), 1)
                if muestreador.vram:
                    resultado["vram_pico_mib"] = round(max(muestreador.vram) - (vram_basal or 0), 1)
            detener(nombre, proceso)
    return resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidatos", type=Path)
    parser.add_argument("salida", type=Path)
    parser.add_argument("--mode", required=True, choices=("cpu", "gpu"))
    parser.add_argument("--limit", type=int)
    parser.add_argument("--peticion", choices=("motor", "benchmark"), default="motor",
                        help="motor: prompt, contexto y response_format de tutor_engine/server.py; benchmark: los de benchmark_tutor_models.py.")
    args = parser.parse_args()
    if args.salida.exists():
        parser.error("La salida ya existe; no se sobrescribe.")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit debe ser positivo.")
    candidatos = json.loads(args.candidatos.read_text(encoding="utf-8"))
    for candidato in candidatos:
        if not {"model_id", "revision", "license", "quantization", "path", "sha256"} <= set(candidato):
            parser.error("Cada candidato requiere modelo, revisión, licencia, cuantización, ruta y sha256.")
        if not re.fullmatch(r"[0-9a-f]{40}", candidato["revision"]):
            parser.error("La revisión de %s no es un hash de 40 hexadecimales." % candidato["model_id"])
        ruta = Path(candidato["path"])
        if not ruta.is_absolute() or not ruta.is_file():
            parser.error("Ruta del modelo inexistente o no absoluta: %s" % candidato["path"])
        if sha256_archivo(ruta) != candidato["sha256"].lower():
            parser.error("El sha256 de %s no coincide con el declarado." % candidato["model_id"])
    crudo = BORRADORES.read_bytes()
    ejemplos = json.loads(crudo.decode("utf-8"))
    if args.limit:
        ejemplos = ejemplos[:args.limit]
    if not ejemplos or any(not {"example_id", *CAMPOS} <= set(item) for item in ejemplos):
        parser.error("Los borradores no tienen la estructura esperada.")
    validar = cargar_guard()
    sistema_motor = prompt_motor()
    imagen =IMAGEN_CPU if args.mode == "cpu" else IMAGEN_GPU
    imagen_id = asegurar_imagen(imagen)
    reportes = []
    try:
        for candidato in candidatos:
            print("Midiendo %s (%s) en modo %s sobre %d borradores..." % (candidato["model_id"], candidato["quantization"], args.mode, len(ejemplos)), flush=True)
            reportes.append(medir_candidato(candidato, args.mode, imagen, ejemplos, validar, args.peticion, sistema_motor))
    except KeyboardInterrupt:
        print("Interrumpido; contenedor detenido, sin salida escrita.")
        raise SystemExit(130)
    informe = {"alcance": "medicion-preliminar-sobre-borradores", "muestra_aprobada": False, "seleccion": "no-realizada",
               "revision_humana": "pendiente", "modo": args.mode, "imagen": imagen, "imagen_id": imagen_id, "limites": LIMITES[args.mode],
               "peticion": {"forma": args.peticion, "max_tokens": 400, "temperature": 0, "seed": 2026, "timeout_s": TIMEOUT_PETICION_S,
                            "presupuesto_motor_ms": PRESUPUESTO_MOTOR_MS, "plazo_anterior_ms": PLAZO_ANTERIOR_MS},
               "hardware": {"plataforma": platform.platform(), "gpu": nombre_gpu(), "cpus_host": os.cpu_count()},
               "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "borradores_sha256": hashlib.sha256(crudo).hexdigest(), "borradores_usados": len(ejemplos), "candidatos": reportes}
    with args.salida.open("x", encoding="utf-8") as flujo:
        json.dump(informe, flujo, indent=2, ensure_ascii=False)
    for reporte in reportes:
        print("%s: carga=%ss p50=%sms p95=%sms errores=%d json=%d guard_rechazos=%d en_0.5s=%d en_8s=%d utiles_motor=%d tok/s=%s ram=%sMiB vram=%sMiB%s" % (
            reporte["candidato"]["model_id"], reporte["tiempo_carga_s"], reporte["latencia_p50_ms"], reporte["latencia_p95_ms"],
            reporte["errores"], reporte["json_valido"], reporte["guard_rechazos"], reporte["dentro_plazo_anterior"],
            reporte["dentro_presupuesto_motor"], reporte["utiles_en_motor"], reporte["tokens_por_segundo_p50"],
            reporte["ram_pico_mib"], reporte["vram_pico_mib"], " ERROR: " + reporte["error_arranque"] if "error_arranque" in reporte else ""))
    print("Medición preliminar: sin aprobación ni selección. Salida: " + str(args.salida))


if __name__ == "__main__":
    main()
