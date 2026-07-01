# CLAUDE.md

## Seguridad — Secrets y variables de entorno

NUNCA leas, muestres, loguees ni hagas referencia al contenido de archivos de secrets:

- `.env`, `.env.local`, `.env.production`, `.env.*`
- Cualquier archivo que contenga claves API, tokens, contraseñas o credenciales

Si necesitas saber qué variables de entorno usa el proyecto, consulta únicamente `src/config.py` o equivalentes — nunca los archivos `.env` reales.
