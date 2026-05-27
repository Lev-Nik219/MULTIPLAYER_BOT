from sqlalchemy import Column, Integer, String, BigInteger, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

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