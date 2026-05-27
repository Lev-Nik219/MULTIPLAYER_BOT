import os
import asyncio
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, PreCheckoutQueryHandler, MessageHandler, filters
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.services.balance import claim_daily_bonus, add_stars

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://frontend-mu-eight-v22bi7khqy.vercel.app")

# Telegram Stars товары
STARS_PRODUCTS: Dict[str, Dict[str, Any]] = {
    "stars_50": {"label": "50 ⭐", "price": 50, "bonus": 0},
    "stars_100": {"label": "105 ⭐", "price": 100, "bonus": 5},
    "stars_250": {"label": "270 ⭐", "price": 250, "bonus": 20},
    "stars_500": {"label": "560 ⭐", "price": 500, "bonus": 60},
}

def get_or_create_user(db: Session, telegram_id: int, username: str) -> User:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username or str(telegram_id),
            balance=5000
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def get_main_keyboard(user_id: int = None) -> InlineKeyboardMarkup:
    webapp_url = f"{WEBAPP_URL}?id={user_id}" if user_id else WEBAPP_URL
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Играть", web_app=WebAppInfo(url=webapp_url))],
        [InlineKeyboardButton("💰 Ежедневный бонус", callback_data="daily")],
        [InlineKeyboardButton("🏆 Топ игроков", callback_data="top"),
         InlineKeyboardButton("📊 Моя статистика", callback_data="stats")],
        [InlineKeyboardButton("👥 Рефералы", callback_data="referrals"),
         InlineKeyboardButton("💎 Пополнить", callback_data="buy")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ])

def get_back_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = SessionLocal()
    get_or_create_user(db, user.id, user.username)
    db.close()
    
    await update.message.reply_text(
        f"🔥 <b>Multiplayer Arena</b>\n\n"
        f"Привет, {user.first_name or user.username}!\n\n"
        f"🎯 <b>Играй и зарабатывай звёзды!</b>\n\n"
        f"⚔️ <b>Доступные игры:</b>\n"
        f"• <code>Дуэль Кликеров</code> — кто быстрее кликает (3⭐)\n"
        f"• <code>Гонки на выживание</code> — набери больше очков (5⭐)\n"
        f"• <code>Кликер Дуэль</code> — классика жанра (2⭐)\n"
        f"• <code>Шахматы на скорость</code> — быстрые партии (10⭐)\n\n"
        f"👇 <b>Выбери действие:</b>",
        reply_markup=get_main_keyboard(user.id),
        parse_mode="HTML"
    )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = SessionLocal()
    
    if query.data == "back":
        await query.edit_message_text(
            "👇 <b>Выбери действие:</b>",
            reply_markup=get_main_keyboard(user_id),
            parse_mode="HTML"
        )
        db.close()
        return
    
    elif query.data == "stats":
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
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=get_back_button())
        
    elif query.data == "daily":
        result = claim_daily_bonus(db, user_id)
        if result["success"]:
            text = f"🎁 <b>Ежедневный бонус!</b>\n\nПолучено: +{result['bonus']}⭐\nТвой баланс: {result['new_balance']}⭐\nСтрик: {result['streak']} дней"
        else:
            text = f"⏰ <b>Ещё рано!</b>\n\n{result['message']}"
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=get_back_button())
        
    elif query.data == "top":
        users = db.query(User).order_by(User.balance.desc()).limit(10).all()
        text = "🏆 <b>Топ игроков по звёздам</b>\n\n"
        for i, u in enumerate(users, 1):
            name = u.username or str(u.telegram_id)
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "▫️"
            text += f"{medal} {i}. {name} — {u.balance}⭐ (Побед: {u.total_wins})\n"
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=get_back_button())
        
    elif query.data == "referrals":
        user = db.query(User).filter(User.telegram_id == user_id).first()
        bot_username = context.bot.username
        text = (
            f"👥 <b>Реферальная программа</b>\n\n"
            f"🏆 <b>Твоя реферальная ссылка:</b>\n"
            f"<code>https://t.me/{bot_username}?start=ref_{user_id}</code>\n\n"
            f"👥 <b>Приглашено друзей:</b> {user.referral_count}\n"
            f"💸 <b>Заработано:</b> {user.referral_earnings}⭐\n\n"
            f"💡 Приглашай друзей и получай 10% от их ставок!"
        )
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=get_back_button())
        
    elif query.data == "buy":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⭐ 50 звёзд", callback_data="buy_50"),
             InlineKeyboardButton("⭐ 105 звёзд (+5)", callback_data="buy_100")],
            [InlineKeyboardButton("⭐ 270 звёзд (+20)", callback_data="buy_250"),
             InlineKeyboardButton("⭐ 560 звёзд (+60)", callback_data="buy_500")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back")]
        ])
        await query.edit_message_text(
            "💎 <b>Пополнение баланса</b>\n\n"
            "Выбери количество звёзд для покупки:\n\n"
            "💰 Оплата через Telegram Stars\n"
            "✨ Мгновенное зачисление",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
    elif query.data.startswith("buy_"):
        product_key = query.data.replace("buy_", "stars_")
        product = STARS_PRODUCTS.get(product_key)
        if product:
            await context.bot.send_invoice(
                chat_id=user_id,
                title="⭐ Пополнение звёзд",
                description=f"Покупка {product['label']} в Multiplayer Arena",
                payload=product_key,
                provider_token="",
                currency="XTR",
                prices=[{"label": product["label"], "amount": product["price"]}],
                start_parameter="stars_payment"
            )
        
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
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=get_back_button())
    
    db.close()

async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    payload = update.message.successful_payment.invoice_payload
    product = STARS_PRODUCTS.get(payload)
    
    if product:
        db = SessionLocal()
        total_stars = product["price"] // 100
        total_stars += product["bonus"]
        add_stars(db, user_id, total_stars)
        db.close()
        
        await update.message.reply_text(
            f"✅ <b>Пополнение успешно!</b>\n\n"
            f"Получено: +{total_stars}⭐\n"
            f"Бонус: +{product['bonus']}⭐\n\n"
            f"Спасибо за покупку! 🎉",
            parse_mode="HTML",
            reply_markup=get_back_button()
        )

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
                    username=user.username or str(user.id),
                    referrer_id=referrer_id,
                    balance=5000
                )
                db.add(new_user)
                db.commit()
                
                # Начисляем бонус рефереру
                referrer.referral_count += 1
                referrer.referral_earnings += 500
                referrer.balance += 500
                db.commit()
                
                await update.message.reply_text(
                    f"🎉 Добро пожаловать!\n\n"
                    f"Тебя пригласил {referrer.username}.\n"
                    f"Ты получил 5⭐ бонус!\n"
                    f"Твой друг получил 5⭐ за приглашение!"
                )
            else:
                await update.message.reply_text("Ты уже зарегистрирован!")
    db.close()
    await start(update, context)

async def main_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", handle_referral))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))
    print("🤖 Бот запущен!")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    while True:
        await asyncio.sleep(1)

def start_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main_bot())