import os
import threading
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import profile, websocket
from app.bot.handlers import start_bot
from app.core.database import init_db, reset_db

# ВРЕМЕННО: сбрасываем БД (один раз, потом закомментируем)
reset_db()  # <-- ЗАКОММЕНТИРУЙ ЭТУ СТРОКУ ПОСЛЕ ПЕРВОГО ЗАПУСКА!

# Инициализация базы данных (создаёт таблицы)
init_db()

# FastAPI приложение
app = FastAPI(title="Multiplayer Arena API", version="2.0.0")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(profile.router, prefix="/api", tags=["profile"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

@app.get("/")
def root():
    return {"message": "Multiplayer Arena API is running", "version": "2.0.0"}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    print("🚀 Запуск сервера...")
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))