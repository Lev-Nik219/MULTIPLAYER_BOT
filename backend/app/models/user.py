from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    balance = Column(Integer, default=5000)
    total_wins = Column(Integer, default=0)
    total_games = Column(Integer, default=0)
    total_losses = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    referrer_id = Column(BigInteger, nullable=True)
    referral_count = Column(Integer, default=0)
    referral_earnings = Column(Integer, default=0)
    last_daily_bonus = Column(DateTime, nullable=True)
    daily_bonus_streak = Column(Integer, default=0)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())