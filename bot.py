from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

TOKEN = "8149438916:AAERXz-gzOy8aPOhBQVCU88Q8EMe_6WMuZs"

NEGATIVE_KEYWORDS = ["ні", "нет", "нецікаво"]
POSITIVE_KEYWORDS = ["так", "да", "цікаво"]
user_states = {}

WELCOME_MESSAGE = """Доброго дня! Ми – Sharry.eu. Наш сайт - це сервіс з бронювання квитків на міжнародні пасажирські перевезення та міжєвропейські напрямки. Як я можу допомогти?"""

INITIAL_REPLY = """Добрий день
Дякуємо за контакт та інтерес до вакансії.

Ось наша сторінка:
🌐 https://sharry.eu/
Також ви можете ознайомитись з нами в соцмережах:
📸 Instagram instagram.com/sharry.eu
🎥 TikTok https://www.tiktok.com/@sharry.eu
Будь ласка, перегляньте нашу платформу та соціальні мережі. Чи цікава вам робота в такій сфері?"""

NEGATIVE_REPLY = "Нічого страшного. Бажаємо успіхів у пошуку роботи. Ви обов'язково знайдете роботу своєї мрії. Бажаю успіхів."

JOB_DESCRIPTION = """Ваша основна роль буде полягати в опрацюванні вхідних запитів, дзвінків та повідомлень, пов'язаних із пошуком поїздок та бронюванням місць.
Самостійно шукати пасажирів Вам НЕ потрібно, ми так не працюємо, пасажири самі приходять на наш сайт!

Робота включатиме:
- Обробку замовлень, які надходять на наш сайт, де пасажири бронюють квитки на автобуси та буси.
- Зв'язок із пасажирами для підтвердження їх замовлень у системі.
- Інформування пасажирів про умови рейсу.
- Надсилання електронних квитків пасажирам.
- Робота з панеллю резервування в кабінеті диспетчера.
- Обслуговування інфолінії.

Чи було б це для вас цікаво?"""

FINAL_REPLY = "Ми готові вас навчити. Для того, щоб отримати доступ до навчальних матеріалів, будь ласка, надішліть документ, що посвідчує вашу особу, на пошту hr@sharry.eu"

# Obsługa komendy /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = "initial"
    await update.message.reply_text(WELCOME_MESSAGE)
    await update.message.reply_text(INITIAL_REPLY)

# Obsługa pozostałych wiadomości
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()

    if user_id not in user_states:
        user_states[user_id] = "initial"
        await update.message.reply_text(INITIAL_REPLY)
        return

    if user_states[user_id] == "initial":
        if any(word in text for word in NEGATIVE_KEYWORDS):
            await update.message.reply_text(NEGATIVE_REPLY)
            user_states[user_id] = "end"
        elif any(word in text for word in POSITIVE_KEYWORDS):
            await update.message.reply_text(JOB_DESCRIPTION)
            user_states[user_id] = "job_sent"
        return

    if user_states[user_id] == "job_sent":
        if any(word in text for word in NEGATIVE_KEYWORDS):
            await update.message.reply_text(NEGATIVE_REPLY)
            user_states[user_id] = "end"
        elif any(word in text for word in POSITIVE_KEYWORDS):
            await update.message.reply_text(FINAL_REPLY)
            user_states[user_id] = "end"
        return

# Uruchomienie aplikacji
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 RekrutacjaSharryBot działa...")
    app.run_polling()
