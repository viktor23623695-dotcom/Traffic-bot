from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import os

BOT_TOKEN = os.getenv("8839936832:AAGd_PNp7dH3klyVfR_WAUubUQwjeVOvji4")
MY_CHANNEL_LINK = "https://t.me/tgpassport_ru"

queue = []
user_states = {}
referrals = {}
referrer_of = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = None
    
    args = context.args
    if args and args[0].startswith("ref_"):
        try:
            referrer_id = int(args[0].split("_")[1])
            if referrer_id != user_id and referrer_id not in referrer_of:
                referrer_of[user_id] = referrer_id
                referrals[referrer_id] = referrals.get(referrer_id, 0) + 1
                await context.bot.send_message(chat_id=referrer_id, text=f"🎉 Новый реферал! @{update.effective_user.username}\nРефералов: {referrals[referrer_id]}/3")
                await check_ref_bonus(referrer_id, context)
        except:
            pass
    
    keyboard = [[InlineKeyboardButton("✅ Я подписался", callback_data="subscribed")]]
    await update.message.reply_text(f"🔥 Добро пожаловать!\n\n🔒 Шаг 1 — подпишись на мой канал:\n{MY_CHANNEL_LINK}\n\n✅ После подписки нажми кнопку:", reply_markup=InlineKeyboardMarkup(keyboard))

async def check_ref_bonus(user_id, context):
    if referrals.get(user_id, 0) >= 3:
        for i, u in enumerate(queue):
            if u["user_id"] == user_id:
                queue.insert(0, queue.pop(i))
                break
        referrals[user_id] = 0
        await context.bot.send_message(chat_id=user_id, text="🏆 Ты привёл 3 участников! Ты в начале очереди!")

async def subscribed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_states[query.from_user.id] = "waiting_link"
    await query.edit_message_text("✅ Хорошо!\n\n📎 Шаг 2 — отправь ссылку на твой канал:")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    link = update.message.text.strip()
    username = update.effective_user.username or f"user{user_id}"
    
    if user_states.get(user_id) != "waiting_link":
        await update.message.reply_text("❌ Нажми /start и пройди все шаги")
        return
    
    if not ("t.me" in link or link.startswith("https://")):
        await update.message.reply_text("❌ Отправь ссылку вида: https://t.me/канал")
        return
    
    queue.append({"user_id": user_id, "link": link, "username": username})
    referrals[user_id] = referrals.get(user_id, 0)
    position = len(queue)
    user_states[user_id] = None
    
    top_users = queue[:3]
    if top_users:
        text = "📌 Шаг 3 — подпишись на этих участников:\n\n"
        for i, u in enumerate(top_users, 1):
            text += f"{i}. {u['link']} (@{u['username']})\n"
        text += "\n✅ После подписки нажми кнопку:"
        keyboard = [[InlineKeyboardButton("✅ Подписался на всех", callback_data="subscribed_to_all")]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("✅ Ты первый в очереди! Жди следующего.")
    
    await update.message.reply_text(f"📊 Твоя позиция: #{position}\n\n🔗 Реферальная ссылка:\nhttps://t.me/{context.bot.username}?start=ref_{user_id}\n\n🎁 Приведи 3 → в начало очереди!\nРефералов: {referrals.get(user_id, 0)} / 3")

async def subscribed_to_all_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    top_users = queue[:3]
    for u in top_users:
        if u["user_id"] != query.from_user.id:
            await context.bot.send_message(chat_id=u["user_id"], text=f"🎉 На твой канал подписался новый участник!\n👤 @{query.from_user.username or 'без ника'}")
    
    await query.edit_message_text("✅ Отлично! Ты выполнил все шаги. Теперь жди подписчиков.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(subscribed_callback, pattern="^subscribed$"))
    app.add_handler(CallbackQueryHandler(subscribed_to_all_callback, pattern="^subscribed_to_all$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    print("✅ Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
