"""Comprueba el motor real sin artefactos: readiness 503 y fallo cerrado."""
import subprocess
import time
import uuid


def main():
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    subprocess.run(["docker", "build", "-f", "tutor_engine/Dockerfile", "--build-arg", "INTEGRATION_COMMIT=" + revision, "-t", "lizardjudge-tutor:local", "."], check=True)
    name = "lizardjudge-engine-check-" + uuid.uuid4().hex[:10]
    subprocess.run(["docker", "run", "-d", "--name", name, "--network", "none", "--read-only", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", "--memory", "256m", "--pids-limit", "64", "lizardjudge-tutor:local"], check=True, stdout=subprocess.DEVNULL)
    code = '''
import json,urllib.request,urllib.error
statuses=[]
for path,body in [('/health',None),('/v1/feedback',{'schema_version':'1.0','action':'concept','level':0,'concept':'fixture','problem':{},'code':'','language':'','diagnostic':{},'concepts':[],'history':[],'config_version':1})]:
    request=urllib.request.Request('http://127.0.0.1:8080'+path,json.dumps(body).encode() if body else None,{'Content-Type':'application/json'})
    try: response=urllib.request.urlopen(request,timeout=3);status=response.status
    except urllib.error.HTTPError as error: status=error.code
    assert status==503,status
    statuses.append(status)
print(json.dumps({'readiness':statuses[0],'feedback':statuses[1],'artifacts_approved':False}))
'''
    try:
        for _ in range(10):
            result = subprocess.run(["docker", "exec", name, "python", "-c", code], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            if result.returncode == 0:
                print(result.stdout.strip())
                return
            time.sleep(1)
        raise RuntimeError("No se comprobó el fallo cerrado del motor.")
    finally:
        subprocess.run(["docker", "rm", "-f", name], check=True, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
