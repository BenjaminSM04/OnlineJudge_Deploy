#!/bin/sh
# Se exige proyecto explícito y un directorio nuevo; nunca se sobrescribe un respaldo.
set -eu
exec python3 "$(dirname "$0")/database.py" backup "$@"
