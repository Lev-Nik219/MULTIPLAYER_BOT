import os
import threading
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import profile, websocket
from app.bot.handlers import start_bot
from app.core.database import engine, Base

# Создание таблиц
Base.metadata.create_all(bind=engine)

# FastAPI приложение
app = FastAPI(title="Multiplayer Arena API", version="1.0.0")

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
    return {"message": "Multiplayer Arena API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

# Запуск бота в фоновом потоке
def run_bot():
    start_bot()

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("🚀 Запуск сервера...")
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))