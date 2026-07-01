#!/bin/bash
# Called from the Makefile's `dev` trap. The frontend runs as a Windows
# process (via cmd.exe interop from WSL), so the WSL-side process group
# kill (`kill 0`) never reaches it — this frees port 5173 from the Windows
# side directly, regardless of which process ended up holding it.
powershell.exe -NoProfile -Command 'Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }' >/dev/null 2>&1
