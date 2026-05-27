from sqlalchemy.orm import Session
from app.models.user import User
from datetime import datetime, timedelta

def get_user_balance(db: Session, telegram_id: int) -> int:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    return user.balance if user else 0

def add_stars(db: Session, telegram_id: int, stars: int, reason: str = None) -> int:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user:
        user.balance += stars
        db.commit()
        return user.balance
    return 0

def deduct_stars(db: Session, telegram_id: int, stars: int) -> bool:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user and user.balance >= stars:
        user.balance -= stars
        db.commit()
        return True
    return False

def add_win(db: Session, telegram_id: int, won_stars: int):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user:
        user.total_wins += 1
        user.total_games += 1
        user.current_streak += 1
        user.best_streak = max(user.best_streak, user.current_streak)
        user.balance += won_stars
        db.commit()
        return True
    return False

def add_loss(db: Session, telegram_id: int):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user:
        user.total_losses += 1
        user.total_games += 1
        user.current_streak = 0
        db.commit()
        return True
    return False

def can_claim_daily_bonus(db: Session, telegram_id: int) -> bool:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user or not user.last_daily_bonus:
        return True
    return datetime.utcnow() - user.last_daily_bonus >= timedelta(days=1)

def claim_daily_bonus(db: Session, telegram_id: int) -> dict:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return {"success": False, "message": "User not found"}
    
    if user.last_daily_bonus and datetime.utcnow() - user.last_daily_bonus < timedelta(days=1):
        next_claim = user.last_daily_bonus + timedelta(days=1)
        return {"success": False, "message": f"Next bonus in {(next_claim - datetime.utcnow()).seconds // 3600} hours"}
    
    # Бонус зависит от стрика
    bonus = 5 + (user.daily_bonus_streak // 7) * 2
    bonus = min(bonus, 25)  # максимум 25 звёзд
    
    user.balance += bonus
    user.daily_bonus_streak += 1
    user.last_daily_bonus = datetime.utcnow()
    db.commit()
    
    return {"success": True, "bonus": bonus, "new_balance": user.balance, "streak": user.daily_bonus_streak}