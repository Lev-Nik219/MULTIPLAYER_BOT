import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Импортируем все модели, чтобы они зарегистрировались в Base
    from app.models import User, GameSession, Tournament
    Base.metadata.create_all(bind=engine)

def reset_db():
    """Удаляет и пересоздаёт все таблицы (только для разработки)"""
    from app.models import User, GameSession, Tournament
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ База данных сброшена и пересоздана!")