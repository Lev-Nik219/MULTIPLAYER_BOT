from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User

router = APIRouter()

@router.get("/profile/{telegram_id}")
def get_profile(telegram_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, balance=5000)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    winrate = round(user.total_wins / max(1, user.total_games) * 100)
    
    return {
        "balance": user.balance,
        "wins": user.total_wins,
        "games": user.total_games,
        "losses": user.total_losses,
        "winrate": winrate,
        "streak": user.current_streak,
        "best_streak": user.best_streak,
        "referral_count": user.referral_count,
        "referral_earnings": user.referral_earnings
    }

@router.post("/balance/add")
def add_balance(telegram_id: int, amount: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.balance += amount
    db.commit()
    return {"new_balance": user.balance}