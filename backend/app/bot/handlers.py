import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://multiplayer-arena.vercel.app")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Играть", web_app=WebAppInfo(url=f"{WEBAPP_URL}?id={user.id}"))],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats"),
         InlineKeyboardButton("👥 Рефералы", callback_data="referrals")],
        [InlineKeyboardButton("💎 Купить звёзды", callback_data="buy")]
    ])
    
    await update.message.reply_text(
        f"🔥 <b>Multiplayer Arena</b>\n\n"
        f"Привет, {user.first_name}!\n\n"
        f"🎯 <b>Твой баланс:</b> 5 ⭐ (бонус)\n"
        f"🏆 <b>Побед:</b> 0\n"
        f"📊 <b>Игр:</b> 0\n\n"
        f"⚔️ <b>Игры доступны:</b>\n"
        f"• <code>Дуэль Кликеров</code> - ставка 3⭐\n"
        f"• <code>Гонки на выживание</code> - ставка 5⭐\n"
        f"• <code>Кликер Дуэль</code> - ставка 2⭐\n"
        f"• <code>Шахматы на скорость</code> - ставка 10⭐\n\n"
        f"💰 Зарабатывай победами и выводи звёзды!",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "stats":
        await query.edit_message_text("📊 Статистика скоро появится!")
    elif query.data == "referrals":
        await query.edit_message_text("👥 Реферальная система в разработке!")
    elif query.data == "buy":
        await query.edit_message_text("💎 Покупка звёзд скоро будет доступна через Telegram Stars!")

def start_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    print("🤖 Бот запущен!")
    app.run_polling()