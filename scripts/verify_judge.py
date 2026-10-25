"""Prueba el protocolo real del juez fijado por digest con fuentes sintéticas."""
import ast
import json
from pathlib import Path
import secrets
import subprocess
import time
import uuid

IMAGE = "registry.cn-hongkong.aliyuncs.com/oj-image/judge:1.6.1@sha256:2dd902870f5e6f69866aa339a6a98b6da9eb1693e2e9936dce23d73203151501"
SOURCES = {
    "C": '#include <stdio.h>\nint main(){int a,b;scanf("%d%d",&a,&b);printf("%d\\n",a+b);}',
    "C++": '#include <iostream>\nint main(){int a,b;std::cin>>a>>b;std::cout<<a+b<<"\\n";}',
    "Java": 'import java.util.*;public class Main{public static void main(String[]args){Scanner s=new Scanner(System.in);System.out.println(s.nextInt()+s.nextInt());}}',
    "Python3": 'a,b=map(int,input().split());print(a+b)',
    "Golang": 'package main\nimport "fmt"\nfunc main(){var a,b int;fmt.Scan(&a,&b);fmt.Println(a+b)}',
    "JavaScript": 'let a=require("fs").readFileSync(0,"utf8").trim().split(/\\s+/).map(Number);console.log(a[0]+a[1]);'
}


def main():
    tree = ast.parse(Path("OnlineJudge/judge/languages.py").read_text(encoding="utf-8"))
    tree.body = [node for node in tree.body if not isinstance(node, (ast.Import, ast.ImportFrom))]
    class ProblemIOMode:
        standard = "Standard IO"
        file = "File IO"
    scope = {"ProblemIOMode": ProblemIOMode}
    exec(compile(tree, "languages.py", "exec"), scope)
    name = "lizardjudge-protocol-" + uuid.uuid4().hex[:10]
    token = secrets.token_urlsafe(32)
    command = ["docker", "run", "-d", "--name", name, "--network", "none", "--read-only", "--pids-limit", "128", "--memory", "1g", "--cpus", "2",
               "--tmpfs", "/judger:size=256m,exec", "--tmpfs", "/log:size=16m", "--tmpfs", "/tmp:size=256m,exec", "-e", "TOKEN=" + token,
               "--cap-drop", "SETPCAP", "--cap-drop", "MKNOD", "--cap-drop", "NET_BIND_SERVICE", "--cap-drop", "SYS_CHROOT", "--cap-drop", "SETFCAP", "--cap-drop", "FSETID",
               "--entrypoint", "sh", IMAGE, "-c", "mkdir -p /judger/run /judger/spj; chown compiler:code /judger/run; chmod 711 /judger/run; cd /app; exec .venv/bin/gunicorn server:app --workers 1 --threads 2 --bind 127.0.0.1:8080 --error-logfile /log/gunicorn.log"]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)
    rows = []
    def call(endpoint, payload, authenticated=True):
        script = '''import os,json,hashlib,urllib.request
payload=json.loads(input())
headers={"Content-Type":"application/json"}
''' + ('headers["X-Judge-Server-Token"]=hashlib.sha256(os.environ["TOKEN"].encode()).hexdigest()\n' if authenticated else "") + '''
req=urllib.request.Request("http://127.0.0.1:8080/''' + endpoint + '''",json.dumps(payload).encode(),headers)
print(urllib.request.urlopen(req,timeout=60).read().decode())
'''
        # Código y payload por stdin separado, sin insertar fuentes en una línea de shell.
        wrapper = "import sys;exec(" + repr(script.replace("payload=json.loads(input())", "payload=" + repr(payload))) + ")"
        result = subprocess.check_output(["docker", "exec", "-i", name, "/app/.venv/bin/python", "-c", wrapper], encoding="utf-8", stderr=subprocess.DEVNULL)
        return json.loads(result)
    try:
        for _ in range(30):
            try:
                if call("ping", {}).get("err") is None:
                    break
            except subprocess.CalledProcessError:
                time.sleep(1)
        else:
            raise RuntimeError("El juez no respondió al ping.")
        assert call("ping", {}, False)["err"] == "TokenVerificationFailed"
        for language in scope["languages"]:
            config = language["config"]
            config["run"]["seccomp_rule"] = config["run"]["seccomp_rule"].get("Standard IO") if isinstance(config["run"]["seccomp_rule"], dict) else config["run"]["seccomp_rule"]
            payload = {"language_config": config, "src": SOURCES[language["name"]], "max_cpu_time": 2000,
                       "max_memory": 256 * 1024 * 1024, "test_case": [{"input": "2 3\n", "output": "5\n"}], "output": False}
            started = time.monotonic()
            result = call("judge", payload)
            passed = result.get("err") is None and all(item["result"] == 0 for item in result["data"])
            rows.append({"language": language["name"], "passed": passed, "elapsed_ms": round((time.monotonic()-started)*1000), "response": result})
        output = Path("respaldos/runtime/judge-protocol.json")
        output.write_text(json.dumps({"image": IMAGE, "network": "none", "root_readonly": True, "synthetic_sources": True, "results": rows}, indent=2), encoding="utf-8")
        if not all(row["passed"] for row in rows):
            raise RuntimeError("Algún lenguaje falló; consulte " + str(output))
        print("OK: protocolo, token y AC real en seis lenguajes. " + str(output))
    finally:
        subprocess.run(["docker", "rm", "-f", name], check=True, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
