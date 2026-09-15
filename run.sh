#!/bin/bash
# ====================================================================
# Script di avvio per GestionePersonaleWeb
# ====================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

PORT=${1:-8080}

echo "===================================================================="
echo " Avvio di Gestione Personale Web su porta $PORT..."
echo "===================================================================="

python3 app/server.py --port "$PORT"

