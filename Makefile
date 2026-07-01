.PHONY: install install-backend install-frontend dev dev-backend dev-frontend test clean docker-dev docker-prod docker-down

install: install-backend install-frontend

install-backend:
	cd backend && uv sync

install-frontend:
	cd frontend && npm install

# Run from a WSL terminal (make and the backend venv both require it — see
# backend/run_dev.sh). Starts backend + frontend together in this one
# terminal: output interleaves, Ctrl+C (or any failure) stops both via the
# trap below. No extra windows.
#
# The frontend runs as a Windows process via cmd.exe interop, so a plain
# `kill 0` (WSL-side process group) never reaches it — kill_frontend_port.sh
# frees its port from the Windows side instead.
dev:
	@trap 'bash kill_frontend_port.sh; kill 0 2>/dev/null; exit 0' EXIT INT TERM; \
	bash backend/run_dev.sh & \
	cmd.exe /c "cd frontend && npm run dev" & \
	wait

dev-backend:
	bash backend/run_dev.sh

dev-frontend:
	cmd.exe /c "cd frontend && npm run dev"

test:
	cd backend && uv run pytest

clean:
	rm -rf backend/.venv backend/.pytest_cache backend/**/__pycache__
	rm -rf frontend/node_modules frontend/dist

# Docker — no WSL needed at all, these run fine directly from PowerShell too
# (`docker compose ...`), `make` is just a shorthand if you already have it.
docker-dev:
	docker compose up --build

docker-prod:
	docker compose -f docker-compose.prod.yml up --build -d

docker-down:
	docker compose down
	docker compose -f docker-compose.prod.yml down
