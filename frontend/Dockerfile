# syntax=docker/dockerfile:1

FROM node:20-slim AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install

# --- dev: bind-mounted source, Vite dev server ---
# --host 0.0.0.0 overrides vite.config.ts's 127.0.0.1 binding (needed there to
# dodge an IPv6-vs-IPv4 localhost mismatch on the host) — inside a container,
# the dev server must listen on all interfaces or Docker's port mapping can't
# reach it.
FROM deps AS dev
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# --- build: production static assets ---
FROM deps AS build
COPY . .
ARG VITE_API_BASE=""
ARG VITE_WS_BASE=""
ENV VITE_API_BASE=$VITE_API_BASE \
    VITE_WS_BASE=$VITE_WS_BASE
RUN npm run build

# --- prod: nginx serving the static build + reverse proxy to backend ---
FROM nginx:1.27-alpine AS prod
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
