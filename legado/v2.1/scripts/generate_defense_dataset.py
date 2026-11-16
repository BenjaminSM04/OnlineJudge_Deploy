"""Genera sintéticos y observa sus veredictos en el mismo juez fijado del sistema."""
import argparse
import ast
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
import subprocess
import time
import uuid

from verify_judge import IMAGE

PROBLEMS = [("suma", "a+b", lambda a, b: a+b), ("producto", "a*b", lambda a, b: a*b),
            ("diferencia", "a-b", lambda a, b: a-b), ("mayor", "(a>b?a:b)", max),
            ("menor", "(a<b?a:b)", min), ("cuadrados", "a*a+b*b", lambda a, b: a*a+b*b)]
HINTS = {
    "compilation": ("Sintaxis y delimitadores", "La compilación se detuvo antes de ejecutar el programa.",
                    ["Recuerda que cada construcción debe respetar la gramática del lenguaje.", "Inspecciona los delimitadores y el final del fragmento.", "Cuenta las aperturas y cierres y vuelve a analizar el primer diagnóstico."]),
    "runtime": ("Ejecución y excepciones", "La ejecución terminó con error; no se deduce una causa distinta de la observada.",
                ["Distingue entre producir una salida y terminar correctamente la ejecución.", "Observa qué instrucción puede interrumpir el flujo del programa.", "Traza el caso público y comprueba hasta qué operación consigue llegar."]),
    "logic": ("Correspondencia entre cálculo y enunciado", "La salida observada difiere de la esperada para el caso público.",
              ["Relaciona la operación pedida con el valor que calcula el programa.", "Inspecciona la expresión que genera el resultado.", "Traza los valores públicos y localiza el primer punto en que el resultado difiere."]),
    "complexity": ("Terminación y progreso", "Se superó el límite temporal durante la ejecución del caso público.",
                   ["Todo recorrido debe progresar hacia una condición de finalización.", "Examina la condición y las variables que cambian durante la repetición.", "Traza dos iteraciones y determina qué tendría que cambiar para que el recorrido termine."])
}


def source(language, expression, mutation, problem):
    if language in ("C", "C++"):
        before = "for(;;){}" if mutation == "loop" else ""
        after = "volatile int z=0; a=a/z;" if mutation == "runtime" else ""
        # La división se ejecuta antes de imprimir para impedir que el optimizador la elimine.
        body = before + after + (f'printf("%d\\n",{expression});' if language == "C" else f'std::cout<<({expression})<<"\\n";')
        code = ('#include <stdio.h>\n' if language == "C" else '#include <iostream>\n') + f'// problema {problem}\nint main(){{int a,b;'
        code += ('scanf("%d%d",&a,&b);' if language == "C" else 'std::cin>>a>>b;') + body + 'return 0;}'
    elif language == "Java":
        before = 'while(a==a){}' if mutation == "loop" else ''
        after = 'int z=0;a=a/z;' if mutation == "runtime" else ''
        code = f'import java.util.*; // problema {problem}\npublic class Main{{public static void main(String[]args){{Scanner s=new Scanner(System.in);int a=s.nextInt(),b=s.nextInt();{before}{after}System.out.println({expression});}}}}'
    elif language == "Python3":
        expr = expression.replace("(a>b?a:b)", "max(a,b)").replace("(a<b?a:b)", "min(a,b)")
        before = 'while True:\n    pass\n' if mutation == "loop" else ''
        after = 'raise RuntimeError("ejecucion sintetica")\n' if mutation == "runtime" else ''
        code = f'# problema {problem}\na,b=map(int,input().split())\n{before}{after}print({expr})'
    elif language == "Golang":
        expr = expression.replace("(a>b?a:b)", "max(a,b)").replace("(a<b?a:b)", "min(a,b)")
        # Go 1.13 del juez no posee min/max: mantener la operación explícita.
        prefix = 'v:=a;if b>a {v=b};' if 'max(a,b)' in expr else ('v:=a;if b<a {v=b};' if 'min(a,b)' in expr else '')
        expr = expr.replace('max(a,b)', 'v').replace('min(a,b)', 'v')
        before = 'for {};' if mutation == "loop" else ''
        after = 'panic("ejecucion sintetica");' if mutation == "runtime" else ''
        code = f'package main\nimport "fmt"\n// problema {problem}\nfunc main(){{var a,b int;fmt.Scan(&a,&b);{prefix}{before}{after}fmt.Println({expr})}}'
    else:
        before = 'while(true){};' if mutation == "loop" else ''
        after = 'throw new Error("ejecucion sintetica");' if mutation == "runtime" else ''
        code = f'// problema {problem}\nlet [a,b]=require("fs").readFileSync(0,"utf8").trim().split(/\s+/).map(Number);{before}{after}console.log({expression});'
    return code + ("\n(" if mutation == "syntax" else "")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("El destino ya existe; no se sobrescribe.")
    args.output.mkdir(parents=True)
    tree = ast.parse(Path("OnlineJudge/judge/languages.py").read_text(encoding="utf-8"))
    tree.body = [node for node in tree.body if not isinstance(node, (ast.Import, ast.ImportFrom))]
    scope = {"ProblemIOMode": type("ProblemIOMode", (), {"standard": "Standard IO", "file": "File IO"})}
    exec(compile(Path("OnlineJudge/judge/language_names.py").read_text(encoding="utf-8"), "names", "exec"), scope)
    exec(compile(tree, "languages", "exec"), scope)
    configs = {}
    for item in scope["languages"]:
        config = item["config"]
        if isinstance(config["run"]["seccomp_rule"], dict):
            config["run"]["seccomp_rule"] = config["run"]["seccomp_rule"]["Standard IO"]
        configs[item["name"]] = config
    name = "lizardjudge-dataset-" + uuid.uuid4().hex[:10]
    env = dict(__import__('os').environ, TOKEN=secrets.token_urlsafe(32))
    command = ["docker", "run", "-d", "--name", name, "--network", "none", "--read-only", "--pids-limit", "128", "--memory", "2g", "--cpus", "2",
               "--tmpfs", "/judger:size=256m,exec", "--tmpfs", "/log:size=32m", "--tmpfs", "/tmp:size=256m,exec", "-e", "TOKEN",
               "--cap-drop", "SETPCAP", "--cap-drop", "MKNOD", "--cap-drop", "NET_BIND_SERVICE", "--cap-drop", "SYS_CHROOT", "--cap-drop", "SETFCAP", "--cap-drop", "FSETID",
               "--entrypoint", "sh", IMAGE, "-c", "mkdir -p /judger/run /judger/spj; chown compiler:code /judger/run; chmod 711 /judger/run; cd /app; exec .venv/bin/gunicorn server:app --workers 1 --threads 2 --timeout 90 --bind 127.0.0.1:8080 --error-logfile /log/gunicorn.log"]
    subprocess.run(command, env=env, check=True, stdout=subprocess.DEVNULL)
    observations, records = [], []
    authored = datetime.now(timezone.utc).isoformat()

    def call(endpoint, payload):
        code = 'import os,json,hashlib,urllib.request; payload=json.loads(input()); req=urllib.request.Request("http://127.0.0.1:8080/' + endpoint + '",json.dumps(payload).encode(),{"Content-Type":"application/json","X-Judge-Server-Token":hashlib.sha256(os.environ["TOKEN"].encode()).hexdigest()});print(urllib.request.urlopen(req,timeout=85).read().decode())'
        raw = subprocess.check_output(["docker", "exec", "-i", name, "/app/.venv/bin/python", "-c", code], input=json.dumps(payload), encoding="utf-8")
        return json.loads(raw)

    def run_job(job):
        index, title, expr, expected, language, mutation = job
        code = source(language, '('+expr+')+1' if mutation == "logic" else expr, mutation, title)
        payload = {"language_config": configs[language], "src": code, "max_cpu_time": 600, "max_memory": 256*1024*1024,
                   "test_case": [{"input": f'{index+3} 2\n', "output": str(expected)+"\n"}], "output": False}
        start = time.monotonic()
        result = call("judge", payload)
        verdict = -2 if result.get("err") == "CompileError" else (result["data"][0]["result"] if result.get("err") is None else 5)
        identifier = f'defensa-{title}-{language.replace("+","p")}-{mutation}'
        observation = {"example_id": identifier, "mutation": mutation, "verdict": verdict, "elapsed_ms": round((time.monotonic()-start)*1000), "source_sha256": hashlib.sha256(code.encode()).hexdigest()}
        if mutation == "control":
            if verdict != 0:
                raise ValueError("El control correcto falló: " + str(observation) + " " + str(result)[:300])
            return observation, None
        category = {-2: "compilation", -1: "logic", 1: "complexity", 2: "complexity", 4: "runtime"}.get(verdict)
        if not category:
            raise ValueError("Veredicto inesperado: " + str(observation) + " " + str(result)[:300])
        concept, explanation, hints = HINTS[category]
        item = {"schema_version": "1.0", "example_id": identifier,
                "problem": f'Leer dos enteros y obtener {title}. Caso público: {index+3} y 2; salida {expected}.', "language": language, "faulty_code": code,
                "verdict": verdict, "category": category, "evidence": [f'Juez fijado por digest: veredicto {verdict} sobre el caso público; control correcto Accepted.'],
                "concept": concept, "explanation": explanation,
                "uncertainty": {"confidence": 0.4, "alternatives": ["Otras causas requieren inspección del fragmento."], "reason": "Demostración sintética observada en el juez; sin validación pedagógica humana."},
                "hints": dict(zip(("concept", "location", "strategy"), hints)),
                "provenance": {"kind": "synthetic", "reference": "generate_defense_dataset.py; " + IMAGE.split('@')[1], "authorization": None},
                "review": {"author": "generacion-sintetica-ejecutada", "authored_at": authored, "reviewer": None, "reviewed_at": None, "approved_at": None,
                           "status": "draft", "notes": "Verificación técnica automatizada; ninguna aprobación humana ni institucional."}}
        return observation, item

    try:
        for _ in range(25):
            try:
                if call("ping", {}).get("err") is None:
                    break
            except subprocess.CalledProcessError:
                time.sleep(1)
        jobs = [(i, title, expr, fn(i+3, 2), language, mutation) for i, (title, expr, fn) in enumerate(PROBLEMS)
                for language in configs for mutation in ("control", "syntax", "logic", "runtime", "loop")]
        with ThreadPoolExecutor(max_workers=2) as pool:
            for observation, item in pool.map(run_job, jobs):
                observations.append(observation)
                if item:
                    records.append(item)
                print(observation["example_id"], observation["verdict"], flush=True)
        (args.output / "examples.json").write_text(json.dumps(records, indent=2, ensure_ascii=True), encoding="utf-8")
        (args.output / "observations.json").write_text(json.dumps({"scope": "technical-demo", "image": IMAGE, "human_approvals": 0, "observations": observations}, indent=2), encoding="utf-8")
        print("OK:", len(records), "borradores observados;", len(observations)-len(records), "controles AC.")
    finally:
        subprocess.run(["docker", "rm", "-f", name], check=True, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
