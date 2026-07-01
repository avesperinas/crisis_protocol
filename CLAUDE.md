# CLAUDE.md

## Security — Secrets and environment variables

NEVER read, display, log or otherwise reference the contents of secret files:

- `.env`, `.env.local`, `.env.production`, `.env.*`
- Any file containing API keys, tokens, passwords or credentials

If you need to know which environment variables the project uses, consult only
`src/config.py` or equivalents — never the real `.env` files.
