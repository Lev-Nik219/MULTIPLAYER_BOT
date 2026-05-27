import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.services.balance import claim_daily_bonus, get_user_balance

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://frontend-mu-eight-v22bi7khqy.vercel.app")

def get_or_create_user(db: Session, telegram_id: int, username: str, first_name: str) -> User:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            balance=5000
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = SessionLocal()
    get_or_create_user(db, user.id, user.username, user.first_name)
    db.close()
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Играть", web_app=WebAppInfo(url=f"{WEBAPP_URL}?id={user.id}"))],
        [InlineKeyboardButton("💰 Ежедневный бонус", callback_data="daily")],
        [InlineKeyboardButton("🏆 Топ игроков", callback_data="top"),
         InlineKeyboardButton("📊 Моя статистика", callback_data="stats")],
        [InlineKeyboardButton("👥 Рефералы", callback_data="referrals"),
         InlineKeyboardButton("💎 Пополнить", callback_data="buy")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ])
    
    await update.message.reply_text(
        f"🔥 <b>Multiplayer Arena</b>\n\n"
        f"Привет, {user.first_name}!\n\n"
        f"🎯 <b>Играй и зарабатывай звёзды!</b>\n\n"
        f"⚔️ <b>Доступные игры:</b>\n"
        f"• <code>Дуэль Кликеров</code> — кто быстрее кликает (3⭐)\n"
        f"• <code>Гонки на выживание</code> — набери больше очков (5⭐)\n"
        f"• <code>Кликер Дуэль</code> — классика жанра (2⭐)\n"
        f"• <code>Шахматы на скорость</code> — быстрые партии (10⭐)\n\n"
        f"🎁 <b>Бонусы:</b>\n"
        f"• Ежедневный бонус — до 25⭐\n"
        f"• Реферальная программа — 10% от ставок друга\n"
        f"• Турниры каждую субботу — большой призовой фонд\n\n"
        f"👇 <b>Выбери действие:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = SessionLocal()
    
    if query.data == "stats":
        user = db.query(User).filter(User.telegram_id == user_id).first()
        winrate = round(user.total_wins / max(1, user.total_games) * 100)
        text = (
            f"📊 <b>Твоя статистика</b>\n\n"
            f"⭐ <b>Баланс:</b> {user.balance}\n"
            f"🏆 <b>Победы:</b> {user.total_wins}\n"
            f"💀 <b>Поражения:</b> {user.total_losses}\n"
            f"📊 <b>Всего игр:</b> {user.total_games}\n"
            f"📈 <b>Winrate:</b> {winrate}%\n"
            f"🔥 <b>Текущая серия:</b> {user.current_streak}\n"
            f"🏅 <b>Лучшая серия:</b> {user.best_streak}\n"
            f"👥 <b>Приглашено друзей:</b> {user.referral_count}\n"
            f"💸 <b>Заработано с рефералов:</b> {user.referral_earnings}⭐"
        )
        await query.edit_message_text(text, parse_mode="HTML")
        
    elif query.data == "daily":
        result = claim_daily_bonus(db, user_id)
        if result["success"]:
            text = f"🎁 <b>Ежедневный бонус!</b>\n\nПолучено: +{result['bonus']}⭐\nТвой баланс: {result['new_balance']}⭐\nСтрик: {result['streak']} дней"
        else:
            text = f"⏰ <b>Ещё рано!</b>\n\n{result['message']}"
        await query.edit_message_text(text, parse_mode="HTML")
        
    elif query.data == "top":
        users = db.query(User).order_by(User.balance.desc()).limit(10).all()
        text = "🏆 <b>Топ игроков по звёздам</b>\n\n"
        for i, u in enumerate(users, 1):
            name = u.first_name or str(u.telegram_id)
            text += f"{i}. {name} — {u.balance}⭐ (Побед: {u.total_wins})\n"
        await query.edit_message_text(text, parse_mode="HTML")
        
    elif query.data == "referrals":
        user = db.query(User).filter(User.telegram_id == user_id).first()
        bot_username = context.bot.username
        text = (
            f"👥 <b>Реферальная программа</b>\n\n"
            f"Приглашай друзей и получай 10% от их ставок!\n\n"
            f"🔗 <b>Твоя ссылка:</b>\n"
            f"<code>https://t.me/{bot_username}?start=ref_{user_id}</code>\n\n"
            f"👥 <b>Приглашено:</b> {user.referral_count}\n"
            f"💸 <b>Заработано:</b> {user.referral_earnings}⭐"
        )
        await query.edit_message_text(text, parse_mode="HTML")
        
    elif query.data == "buy":
        text = (
            "💎 <b>Пополнение баланса</b>\n\n"
            "Пополнение через Telegram Stars:\n\n"
            "• 50⭐ — 50 звёзд\n"
            "• 100⭐ — 105 звёзд (+5 бонус)\n"
            "• 250⭐ — 270 звёзд (+20 бонус)\n"
            "• 500⭐ — 560 звёзд (+60 бонус)\n\n"
            "Скоро будет доступно!"
        )
        await query.edit_message_text(text, parse_mode="HTML")
        
    elif query.data == "help":
        text = (
            "ℹ️ <b>Помощь</b>\n\n"
            "🎮 <b>Как играть?</b>\n"
            "1. Нажми 'Играть'\n"
            "2. Выбери игру и ставку\n"
            "3. Жди соперника\n"
            "4. Кликай быстрее!\n\n"
            "💰 <b>Как заработать?</b>\n"
            "• Победы в играх\n"
            "• Ежедневные бонусы\n"
            "• Реферальная программа\n"
            "• Турниры\n\n"
            "❓ Вопросы? Пиши @support"
        )
        await query.edit_message_text(text, parse_mode="HTML")
    
    db.close()

async def handle_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    referrer_id = context.args[0] if context.args else None
    if referrer_id and referrer_id.isdigit():
        referrer_id = int(referrer_id)
        referrer = db.query(User).filter(User.telegram_id == referrer_id).first()
        if referrer:
            user = update.effective_user
            existing = db.query(User).filter(User.telegram_id == user.id).first()
            if not existing:
                new_user = User(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    referrer_id=referrer_id,
                    balance=5000
                )
                db.add(new_user)
                db.commit()
                await update.message.reply_text(
                    f"🎉 Добро пожаловать!\n\nТебя пригласил {referrer.first_name}.\nТы получил 5⭐ бонус!"
                )
            else:
                await update.message.reply_text("Ты уже зарегистрирован!")
    db.close()
    await start(update, context)

async def main_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", handle_referral))
    app.add_handler(CallbackQueryHandler(callback_handler))
    print("🤖 Бот запущен!")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    # Keep running
    while True:
        await asyncio.sleep(1)

def start_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main_bot())