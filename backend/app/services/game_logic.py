import secrets
from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.game import GameSession
from app.services.balance import add_win, add_loss, deduct_stars

# Матчмейкинг очереди
matchmaking_queue: Dict[str, list] = {
    "duel_clicker": [],
    "clicker_duel": [],
    "survival_race": [],
    "chess_fast": []
}

# Активные игры
active_games: Dict[str, 'DuelClickerGame'] = {}

def get_queue_size(game_type: str) -> int:
    return len(matchmaking_queue.get(game_type, []))

def add_to_queue(telegram_id: int, game_type: str, bet: int, db: Session) -> Optional[int]:
    """Добавляет игрока в очередь. Возвращает ID соперника если найден"""
    queue = matchmaking_queue.get(game_type, [])
    
    # Проверяем баланс
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user or user.balance < bet:
        return None
    
    # Ищем соперника с такой же ставкой
    for i, (q_id, q_bet) in enumerate(queue):
        if q_bet == bet:
            opponent = queue.pop(i)
            return opponent[0]
    
    # Не нашли — добавляем в очередь
    queue.append((telegram_id, bet))
    return None

def remove_from_queue(telegram_id: int, game_type: str):
    queue = matchmaking_queue.get(game_type, [])
    matchmaking_queue[game_type] = [q for q in queue if q[0] != telegram_id]

def create_game_session(db: Session, game_id: str, game_type: str, player1: int, player2: int, bet: int) -> GameSession:
    session = GameSession(
        game_id=game_id,
        game_type=game_type,
        player1_id=player1,
        player2_id=player2,
        bet=bet,
        status="active"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Списываем ставки
    for pid in [player1, player2]:
        deduct_stars(db, pid, bet)
    
    return session

def finish_game(db: Session, game_id: str, winner_id: int, player1_score: int, player2_score: int) -> dict:
    session = db.query(GameSession).filter(GameSession.game_id == game_id).first()
    if not session:
        return {"success": False, "message": "Game not found"}
    
    session.status = "finished"
    session.winner_id = winner_id
    session.player1_score = player1_score
    session.player2_score = player2_score
    session.finished_at = datetime.utcnow()
    
    # Начисляем выигрыш (ставка * 2 - комиссия 5%)
    prize = int(session.bet * 2 * 0.95)
    add_win(db, winner_id, prize)
    
    loser_id = session.player2_id if session.player1_id == winner_id else session.player1_id
    add_loss(db, loser_id)
    
    db.commit()
    
    return {
        "success": True,
        "winner": winner_id,
        "prize": prize,
        "player1_score": player1_score,
        "player2_score": player2_score,
        "bet": session.bet
    }

class DuelClickerGame:
    def __init__(self, game_id: str, player1: int, player2: int, bet: int, duration: int = 30):
        self.game_id = game_id
        self.player1 = player1
        self.player2 = player2
        self.bet = bet
        self.duration = duration
        self.scores = {player1: 0, player2: 0}
        self.active = True
        self.start_time = datetime.utcnow()
    
    def add_click(self, player_id: int) -> dict:
        if not self.active:
            return {"success": False, "message": "Game finished"}
        self.scores[player_id] += 1
        return {"success": True, "score": self.scores[player_id]}
    
    def get_state(self) -> dict:
        elapsed = (datetime.utcnow() - self.start_time).seconds
        remaining = max(0, self.duration - elapsed)
        return {
            "active": self.active and remaining > 0,
            "remaining": remaining,
            "scores": self.scores,
            "duration": self.duration
        }
    
    def finish(self, db: Session) -> dict:
        self.active = False
        if self.scores[self.player1] > self.scores[self.player2]:
            winner = self.player1
        elif self.scores[self.player2] > self.scores[self.player1]:
            winner = self.player2
        else:
            # Ничья — возвращаем ставки
            deduct_stars(db, self.player1, -self.bet)
            deduct_stars(db, self.player2, -self.bet)
            return {"success": True, "draw": True, "message": "Draw! Bets returned"}
        
        return finish_game(db, self.game_id, winner, self.scores[self.player1], self.scores[self.player2])
    
    @staticmethod
    def create(db: Session, game_id: str, player1: int, player2: int, bet: int) -> 'DuelClickerGame':
        create_game_session(db, game_id, "duel_clicker", player1, player2, bet)
        return DuelClickerGame(game_id, player1, player2, bet)