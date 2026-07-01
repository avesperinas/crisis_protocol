# Crisis Protocol

A real-time multiplayer geopolitical negotiation game. Each player controls a
faction during an international crisis and competes — and cooperates — for their
objectives through directives, pacts and partial information. Factions without a
human player are controlled by a Claude-powered bot, which also generates each
turn's briefing, intelligence reports and resolution narrative.

The whole experience is localized: each game runs in a single language (English
or Spanish), chosen at creation, and every AI-generated, player-facing text is
written in that language to stay immersive.

## Stack

- **Backend** — Python 3.12, FastAPI, SQLAlchemy (SQLite + aiosqlite), WebSockets,
  JWT auth, and the [Anthropic](https://docs.anthropic.com) SDK for the AI.
- **Frontend** — React 19, TypeScript, Vite, Tailwind CSS, Zustand, React Router
  and i18n (Spanish / English).
- **Infra** — Docker / Docker Compose for development and production.

## Scenarios

Three playable scenarios ship with the game, each with its own factions,
objectives and events: **Arctic Crisis (2031)**, **The Congress of Corinth
(338 BCE)** and **The Oil Crisis (1973)**.

## Requirements

- [uv](https://docs.astral.sh/uv/) (Python dependency manager)
- Node.js 20+
- An `ANTHROPIC_API_KEY` for the AI features
- Optional: Docker + Docker Compose

## Configuration

Copy the backend environment template and fill in your key:

```bash
cp backend/.env.example backend/.env
# edit backend/.env and set ANTHROPIC_API_KEY
```

See `backend/src/config.py` for the full list of supported variables and their
defaults. The real `.env` is **never** committed (it is in `.gitignore`); for
production use `backend/.env.prod.example` as a reference.

## Development

### With Docker (recommended, cross-platform)

```bash
docker compose up --build
```

- Backend: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:5173

### Without Docker

```bash
make install        # uv sync (backend) + npm install (frontend)
make dev            # start backend and frontend together
```

Or separately:

```bash
make dev-backend    # uvicorn on :8000
make dev-frontend   # vite on :5173
```

## Tests

```bash
make test           # backend pytest suite
```

## Production

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

Remember to generate your own `JWT_SECRET_KEY` before deploying (the default is
insecure and only meant for local development).

## License

[Apache License 2.0](LICENSE).
