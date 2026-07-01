#!/bin/bash
# Run via `make dev` / `make dev-backend` from a WSL terminal.
export PATH="$HOME/.local/bin:$PATH"
cd "$(dirname "$0")"

pkill -9 -f "uvicorn src.main" 2>/dev/null
sleep 1

echo "Backend en http://127.0.0.1:8000"
echo "Nota: --reload no detecta cambios hechos desde Windows en este mount WSL."
echo "Si editas codigo del backend, reinicia con Ctrl+C y volviendo a ejecutar make dev."
echo

uv run uvicorn src.main:app --reload --port 8000
