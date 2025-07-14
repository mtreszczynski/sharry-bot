from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

TOKEN = "8149438916:AAERXz-gzOy8aPOhBQVCU88Q8EMe_6WMuZs"

# Słowa kluczowe (rozszerzone)
NEGATIVE_KEYWORDS = ["ні", "нет", "нецікаво", "ni", "net", "no"]
POSITIVE_KEYWORDS = ["так", "да", "цікаво", "tak", "da", "yes"]

# Przechowywanie stanu konwersacji
user_states = {}

# Wiadomości
INITIAL_MESSAGE = """Добрий день 
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
-Обробку замовлень, які надходять на наш сайт, де пасажири бронюють квитки на автобуси та буси.
-Зв'язок із пасажирами для підтвердження їх замовлень у системі.
-Інформування пасажирів про умови рейсу.
-Надсилання електронних квитків пасажирам.
-Робота з панеллю резервування в кабінеті диспетчера.
-Обслуговування інфолінії.

Чи буде це для вас цікаво?"""

QUESTIONS = """Розкажіть трохи про себе і домовимось про телефонну розмову)

-З якого ви міста? 
-Скільки вам років? 
-Яка ваша освіта?
-Розкажіть про ваш досвід роботи. Чи був досвід віддаленої роботи?
-Чи мали ви досвід роботи з таблицями Google або Excel?
-Чи є у вас доступ до комп'ютера?
-Як ви впораєтеся з ситуаціями вимкнення світла?  Чи є у вас запасні варіанти для продовження роботи?
-Яка ваша доступність для роботи протягом дня (скільки годин на день і в якій половині дня)?"""

FINAL_REPLY = "Ми готові вас навчити. Для того, щоб отримати доступ до навчальних матеріалів, будь ласка, надішліть документ, що посвідчує вашу особу, на пошту hr@sharry.eu"

# Obsługa komendy /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = "initial"
    await update.message.reply_text(INITIAL_MESSAGE)

# Obsługa wiadomości
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()

    state = user_states.get(user_id, "initial")

    # Etap 1: po wiadomości powitalnej
    if state == "initial":
        if any(word in text for word in NEGATIVE_KEYWORDS):
            await update.message.reply_text(NEGATIVE_REPLY)
            user_states[user_id] = "end"
        elif any(word in text for word in POSITIVE_KEYWORDS):
            await update.message.reply_text(JOB_DESCRIPTION)
            user_states[user_id] = "job_sent"
        return

    # Etap 2: po opisie pracy
    if state == "job_sent":
        if any(word in text for word in NEGATIVE_KEYWORDS):
            await update.message.reply_text(NEGATIVE_REPLY)
            user_states[user_id] = "end"
        elif any(word in text for word in POSITIVE_KEYWORDS):
            await update.message.reply_text(QUESTIONS)
            user_states[user_id] = "questions_sent"
        return

    # Etap 3: kandydat odpowiada na pytania
    if state == "questions_sent":
        await update.message.reply_text(FINAL_REPLY)
        user_states[user_id] = "end"
        return

# Uruchomienie bota
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 RekrutacjaSharryBot działa...")
    app.run_polling()
