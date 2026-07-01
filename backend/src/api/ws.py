"""WebSocket endpoint — clients connect here to receive real-time game events."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.services.connection_manager import manager

logger = logging.getLogger("crisis.ws")

router = APIRouter(tags=["ws"])


@router.websocket("/ws/games/{game_id}")
async def ws_game(websocket: WebSocket, game_id: str, role_id: str) -> None:
    """
    Persistent connection per player. The server pushes JSON events:
      {"type": "state_updated"}        — re-fetch game state
      {"type": "action_submitted", "role_id": "..."}  — another player acted
      {"type": "game_started"}         — lobby → active transition
    Clients send "ping" and receive "pong" for keep-alive.
    """
    await manager.connect(game_id, role_id, websocket)
    try:
        while True:
            text = await websocket.receive_text()
            if text == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(game_id, role_id)
