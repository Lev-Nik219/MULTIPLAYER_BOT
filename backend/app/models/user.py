from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    
    # Баланс и статистика
    balance = Column(Integer, default=5000)  # в звёздах
    total_wins = Column(Integer, default=0)
    total_games = Column(Integer, default=0)
    total_losses = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    
    # Реферальная система
    referrer_id = Column(BigInteger, nullable=True)
    referral_count = Column(Integer, default=0)
    referral_earnings = Column(Integer, default=0)
    
    # Ежедневные бонусы
    last_daily_bonus = Column(DateTime, nullable=True)
    daily_bonus_streak = Column(Integer, default=0)
    
    # Другое
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class GameSession(Base):
    __tablename__ = "game_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, unique=True, index=True)
    game_type = Column(String)
    player1_id = Column(BigInteger)
    player2_id = Column(BigInteger, nullable=True)
    bet = Column(Integer)
    status = Column(String, default="waiting")  # waiting, active, finished, cancelled
    winner_id = Column(BigInteger, nullable=True)
    player1_score = Column(Integer, default=0)
    player2_score = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    finished_at = Column(DateTime, nullable=True)

class Tournament(Base):
    __tablename__ = "tournaments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    game_type = Column(String)
    entry_fee = Column(Integer)
    prize_pool = Column(Integer)
    max_players = Column(Integer)
    current_players = Column(Integer, default=0)
    status = Column(String, default="pending")  # pending, active, finished
    winner_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)