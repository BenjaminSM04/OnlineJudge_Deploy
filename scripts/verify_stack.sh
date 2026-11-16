#!/usr/bin/env bash
# Levanta el stack en un proyecto aislado con secretos de prueba y comprueba que
# la interfaz, la API, el registro de usuarios y el juez respondan.
# Uso: bash scripts/verify_stack.sh [proyecto] [puerto]
# No toca el .env real ni los volúmenes de otra instalación.
set -euo pipefail

proyecto="${1:-lizardjudge-prueba}"
puerto="${2:-18090}"
raiz="$(cd "$(dirname "$0")/.." && pwd)"
cd "$raiz"
mkdir -p .verification
entorno=".verification/ci.env"

secreto() { python3 -c "import secrets; print(secrets.token_urlsafe($1))"; }
cat > "$entorno" <<EOF
POSTGRES_PASSWORD=$(secreto 24)
JUDGE_SERVER_TOKEN=$(secreto 40)
OJ_HTTP_PORT=$puerto
OJ_HTTP_BIND=127.0.0.1
EOF

compose=(docker compose -p "$proyecto" --env-file "$entorno")
"${compose[@]}" -f docker-compose.yml -f compose.tutor.yml config -q
"${compose[@]}" up -d --build --wait --wait-timeout 600

base="http://127.0.0.1:$puerto"
curl -fsS "$base/healthz" > /dev/null
curl -fsS "$base/" | grep -qi "<html" || { echo "La interfaz no devolvió HTML"; exit 1; }
curl -fsS "$base/api/website" | grep -q '"error": *null' || { echo "La API no respondió"; exit 1; }

# El juez se registra con un latido: esperar a que el backend lo vea.
for _ in $(seq 1 30); do
  if "${compose[@]}" exec -T oj-backend python manage.py shell -c \
      "from conf.models import JudgeServer; import sys; sys.exit(0 if JudgeServer.objects.exists() else 1)" 2>/dev/null; then
    echo "Stack verificado en $base (interfaz, API y juez)."
    exit 0
  fi
  sleep 5
done
echo "El juez no envió latidos al backend."
exit 1
