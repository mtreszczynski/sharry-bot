from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

TOKEN = "8149438916:AAERXz-gzOy8aPOhBQVCU88Q8EMe_6WMuZs"

# Kluczowe słowa
NEGATIVE_KEYWORDS = ["ні", "нет", "нецікаво"]
POSITIVE_KEYWORDS = ["так", "да", "цікаво"]

# Śledzenie etapów dla każdego użytkownika
user_states = {}

# Wiadomości
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
- Обслуговування інфолінії."""

FINAL_REPLY = "Ми готові вас навчити. Для того, щоб отримати доступ до навчальних матеріалів, будь ласка, надішліть документ, що посвідчує вашу особу, на пошту hr@sharry.eu"

# Obsługa wiadomości
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()

    # Pierwszy kontakt
    if user_id not in user_states:
        user_states[user_id] = "initial"
        await update.message.reply_text(INITIAL_REPLY)
        return

    # Etap 1: pytanie o zainteresowanie
    if user_states[user_id] == "initial":
        if any(word in text for word in NEGATIVE_KEYWORDS):
            await update.message.reply_text(NEGATIVE_REPLY)
            user_states[user_id] = "end"
        elif any(word in text for word in POSITIVE_KEYWORDS):
            await update.message.reply_text(JOB_DESCRIPTION)
            user_states[user_id] = "job_sent"
        return

    # Etap 2: po opisie pracy
    if user_states[user_id] == "job_sent":
        if any(word in text for word in NEGATIVE_KEYWORDS):
            await update.message.reply_text(NEGATIVE_REPLY)
            user_states[user_id] = "end"
        elif any(word in text for word in POSITIVE_KEYWORDS):
            await update.message.reply_text(FINAL_REPLY)
            user_states[user_id] = "end"
        return

# Uruchomienie bota
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 RekrutacjaSharryBot działa...")
    app.run_polling()
