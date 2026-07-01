"""WebSocket connection manager — tracks live connections per game."""

import logging
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("crisis.ws")


class ConnectionManager:
    def __init__(self) -> None:
        # game_id → {role_id → WebSocket}
        self._connections: dict[str, dict[str, WebSocket]] = defaultdict(dict)

    async def connect(self, game_id: str, role_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections[game_id][role_id] = ws
        logger.info("WS connect: game=%s role=%s", game_id, role_id)

    def disconnect(self, game_id: str, role_id: str) -> None:
        self._connections[game_id].pop(role_id, None)
        if not self._connections[game_id]:
            self._connections.pop(game_id, None)
        logger.info("WS disconnect: game=%s role=%s", game_id, role_id)

    async def broadcast(self, game_id: str, data: dict[str, Any]) -> None:
        dead: list[str] = []
        for role_id, ws in list(self._connections.get(game_id, {}).items()):
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(role_id)
        for role_id in dead:
            self.disconnect(game_id, role_id)

    def connected_roles(self, game_id: str) -> list[str]:
        return list(self._connections.get(game_id, {}).keys())


manager = ConnectionManager()
