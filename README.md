# Crisis Protocol

Juego multijugador de negociación geopolítica en tiempo real. Cada jugador
controla una facción durante una crisis internacional y compite —y coopera—
por sus objetivos a través de directivas, pactos e información parcial. Las
facciones sin jugador humano las controla un bot impulsado por Claude, que
también genera el briefing, los informes de inteligencia y la narrativa de
resolución de cada turno.

## Stack

- **Backend** — Python 3.12, FastAPI, SQLAlchemy (SQLite + aiosqlite), WebSockets,
  autenticación JWT y el SDK de [Anthropic](https://docs.anthropic.com) para la IA.
- **Frontend** — React 19, TypeScript, Vite, Tailwind CSS, Zustand, React Router
  e i18n (español / inglés).
- **Infra** — Docker / Docker Compose para desarrollo y producción.

## Escenarios

Incluye tres escenarios jugables, cada uno con sus facciones, objetivos y
eventos: **Ártico 2031**, **Corinto** y **Crisis del petróleo**.

## Requisitos

- [uv](https://docs.astral.sh/uv/) (gestor de dependencias de Python)
- Node.js 20+
- Una `ANTHROPIC_API_KEY` para las funciones de IA
- Opcional: Docker + Docker Compose

## Configuración

Copia la plantilla de variables de entorno del backend y rellena tu clave:

```bash
cp backend/.env.example backend/.env
# edita backend/.env y define ANTHROPIC_API_KEY
```

Consulta `backend/src/config.py` para la lista completa de variables soportadas
y sus valores por defecto. **Nunca** se commitea el `.env` real (está en
`.gitignore`); para producción usa `backend/.env.prod.example` como referencia.

## Desarrollo

### Con Docker (recomendado, multiplataforma)

```bash
docker compose up --build
```

- Backend: http://localhost:8000 (docs en `/docs`)
- Frontend: http://localhost:5173

### Sin Docker

```bash
make install        # uv sync (backend) + npm install (frontend)
make dev            # arranca backend y frontend juntos
```

O por separado:

```bash
make dev-backend    # uvicorn en :8000
make dev-frontend   # vite en :5173
```

## Tests

```bash
make test           # pytest del backend
```

## Producción

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

Recuerda generar un `JWT_SECRET_KEY` propio antes de desplegar (el valor por
defecto es inseguro y solo sirve para desarrollo local).

## Licencia

[Apache License 2.0](LICENSE).
