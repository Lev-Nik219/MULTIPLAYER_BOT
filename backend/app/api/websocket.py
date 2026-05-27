from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import json

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        self.active_connections.pop(user_id, None)

    async def send_message(self, user_id: int, message: dict):
        if ws := self.active_connections.get(user_id):
            await ws.send_json(message)

manager = ConnectionManager()

@router.websocket("/{telegram_id}")
async def websocket_endpoint(websocket: WebSocket, telegram_id: int):
    await manager.connect(websocket, telegram_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await manager.send_message(telegram_id, {"type": "echo", "data": message})
    except WebSocketDisconnect:
        manager.disconnect(telegram_id)