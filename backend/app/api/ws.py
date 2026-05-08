"""WebSocket endpoint - pushes live suggestions/QR updates to frontend."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Dict, Set

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_access_token
from app.db.redis import get_redis

log = logging.getLogger(__name__)

router = APIRouter(tags=["ws"])

# user_id -> set of websockets
_clients: Dict[int, Set[WebSocket]] = {}


async def push_to_user(user_id: int, event: dict) -> None:
    """Server-side helper. Also publishes via redis so other workers can fan-out."""
    payload = json.dumps(event)
    await get_redis().publish(f"ws:user:{user_id}", payload)
    for ws in list(_clients.get(user_id, set())):
        try:
            await ws.send_text(payload)
        except Exception:
            _clients.get(user_id, set()).discard(ws)


@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket, token: str = Query(...)):
    try:
        data = decode_access_token(token)
        user_id = int(data["sub"])
    except Exception:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    _clients.setdefault(user_id, set()).add(websocket)

    pubsub = get_redis().pubsub()
    await pubsub.subscribe(f"ws:user:{user_id}")

    async def relay() -> None:
        async for msg in pubsub.listen():
            if msg.get("type") == "message":
                try:
                    await websocket.send_text(msg["data"])
                except Exception:
                    return

    relay_task = asyncio.create_task(relay())
    try:
        while True:
            # we don't expect inbound messages but keep the loop alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        relay_task.cancel()
        try:
            await pubsub.unsubscribe(f"ws:user:{user_id}")
            await pubsub.close()
        except Exception:
            pass
        _clients.get(user_id, set()).discard(websocket)
