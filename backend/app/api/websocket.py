from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import json
import secrets
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.game_logic import (
    add_to_queue, remove_from_queue, get_queue_size,
    active_games, DuelClickerGame
)

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
    db = SessionLocal()
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            cmd = message.get("cmd")
            
            if cmd == "find_match":
                game_type = message.get("game_type")
                bet = message.get("bet")
                
                # Добавляем в очередь
                opponent = add_to_queue(telegram_id, game_type, bet, db)
                
                if opponent is not None:
                    # Найден соперник — создаём игру
                    game_id = secrets.token_hex(8)
                    game = DuelClickerGame.create(db, game_id, telegram_id, opponent, bet)
                    active_games[game_id] = game
                    
                    # Уведомляем обоих игроков
                    await manager.send_message(telegram_id, {
                        "type": "match_found",
                        "game_id": game_id,
                        "opponent": opponent,
                        "bet": bet,
                        "duration": game.duration
                    })
                    await manager.send_message(opponent, {
                        "type": "match_found",
                        "game_id": game_id,
                        "opponent": telegram_id,
                        "bet": bet,
                        "duration": game.duration
                    })
                else:
                    # В очереди
                    await manager.send_message(telegram_id, {
                        "type": "searching",
                        "queue_size": get_queue_size(game_type)
                    })
            
            elif cmd == "cancel_search":
                game_type = message.get("game_type")
                remove_from_queue(telegram_id, game_type)
                await manager.send_message(telegram_id, {"type": "search_cancelled"})
            
            elif cmd == "game_click":
                game_id = message.get("game_id")
                game = active_games.get(game_id)
                if game:
                    result = game.add_click(telegram_id)
                    if result["success"]:
                        opponent = game.player1 if game.player2 == telegram_id else game.player2
                        await manager.send_message(opponent, {
                            "type": "opponent_click",
                            "score": result["score"]
                        })
                        await manager.send_message(telegram_id, {
                            "type": "your_click",
                            "score": result["score"]
                        })
                    
                    # Проверяем окончание игры
                    state = game.get_state()
                    if not state["active"]:
                        result = game.finish(db)
                        await manager.send_message(game.player1, {
                            "type": "game_finished",
                            **result,
                            "your_score": game.scores[game.player1],
                            "opponent_score": game.scores[game.player2]
                        })
                        await manager.send_message(game.player2, {
                            "type": "game_finished",
                            **result,
                            "your_score": game.scores[game.player2],
                            "opponent_score": game.scores[game.player1]
                        })
                        del active_games[game_id]
            
            elif cmd == "game_state":
                game_id = message.get("game_id")
                game = active_games.get(game_id)
                if game:
                    await manager.send_message(telegram_id, {
                        "type": "game_state",
                        **game.get_state()
                    })
                    
    except WebSocketDisconnect:
        manager.disconnect(telegram_id)
        remove_from_queue(telegram_id, "")
    finally:
        db.close()