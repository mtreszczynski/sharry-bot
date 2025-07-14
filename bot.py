import os
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

# ── TELEGRAM ────────────────────────────────────────────────────────────────
TOKEN = os.environ["TELEGRAM_TOKEN"]

# ── GOOGLE SHEETS ───────────────────────────────────────────────────────────
GOOGLE_SECRET_FILE = "/etc/secrets/GOOGLE_CREDENTIALS"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SECRET_FILE, SCOPES)
client = gspread.authorize(creds)
sheet = client.open("RekrutacjaSharryBot").sheet1

# ── REKRUTACJA ─────────────────────────────────────────────────────────────
NEGATIVE_KEYWORDS = ["ні", "нет", "нецікаво", "ni", "net", "no"]
POSITIVE_KEYWORDS = ["так", "да", "цікаво", "tak", "da", "yes"]

# przechowuje stan: "initial", "job_sent", "q_0", "q_1", ..., "end"
user_states = {}

INITIAL_MESSAGE = """\
Добрий день 
Дякуємо за контакт та інтерес до вакансії.

Ось наша сторінка:
🌐 https://sharry.eu/
📸 Instagram instagram.com/sharry.eu
🎥 TikTok https://www.tiktok.com/@sharry.eu

Будь ласка, перегляньте нашу платформу та соціальні мережі.
Чи цікава вам робота в такій сфері?
"""

NEGATIVE_REPLY = (
    "Нічого страшного. Бажаємо успіхів у пошуку роботи. "
    "Ви обов'язково знайдете роботу своєї мрії. Бажаю успіхів."
)

JOB_DESCRIPTION = """\
Ваша основна роль буде полягати в опрацюванні вхідних запитів, дзвінків та повідомлень, пов'язаних із пошуком поїздок та бронюванням місць.
Самостійно шукати пасажирів Вам НЕ потрібно, ми так не працюємо, пасажири самі приходять на наш сайт. Також важливо, що для роботи необхідний власний комп'ютер, з телефону працювати не можна.!

Робота включатиме:
-Обробку замовлень, які надходять на наш сайт, де пасажири бронюють квитки на автобуси та буси.
-Зв'язок із пасажирами для підтвердження їх замовлень у системі.
-Інформування пасажирів про умови рейсу.
-Надсилання електронних квитків пасажирам.
-Робота з панеллю резервування в кабінеті диспетчера.
-Обслуговування інфолінії.

Чи буде це для вас цікаво?"""

# lista pytań – dokładnie ta sama treść, tylko rozbita na 11 elementów
QUESTIONS_LIST = [
    "Чудово! Тоді пропоную трохи ближче познайомитись. Розкажіть, будь ласка, кілька слів про себе, а також дайте відповіді на короткі запитання нижче — і ми домовимось про телефонну розмову:\n\n1. Звідки Ви? (місто)",
    "2. Ваш вік",
    "3. Освіта (спеціальність)",
    "4. Ваш досвід роботи:",
    "5. Чи мали Ви досвід віддаленої роботи?",
    "6. Чи працювали з CRM-системами?",
    "7. Чи мали досвід з телефонією або кол-центрами (дзвінки, IP-телефонія)?",
    "8. Чи маєте доступ до комп’ютера/ноутбуку та стабільного інтернету? (робота з телефону неможлива!)",
    "9. Скільки годин можете приділяти роботі?",
    "10. В який час (день/вечір/ніч) Вам зручніше працювати?",
    "11. Номер телефону, за яким наш співробітник може зателефонувати, щоб обговорити деталі."
]

FINAL_REPLY = """\
Дякуємо за ваші відповіді. Ви дуже цікавий кандидат :)
Якщо ви хочете отримати доступ до навчальних матеріалів, щоб краще зрозуміти, чи підходить вам ця робота, така можливість є. Для цього необхідно підписати угоду про конфіденційність. Якщо ви зацікавлені, надішліть відповідний запит на адресу hr@sharry.eu.
"""

def log_user_response(user_id: int, username: str, text: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([ts, str(user_id), username or "-", text])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_states[uid] = "initial"
    await update.message.reply_text(INITIAL_MESSAGE)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.lower()
    username = update.effective_user.username or "-"
    log_user_response(uid, username, text)

    state = user_states.get(uid, "initial")

    # etap 1: po /start
    if state == "initial":
        if any(w in text for w in NEGATIVE_KEYWORDS):
            await update.message.reply_text(NEGATIVE_REPLY)
            user_states[uid] = "end"
        elif any(w in text for w in POSITIVE_KEYWORDS):
            await update.message.reply_text(JOB_DESCRIPTION)
            user_states[uid] = "job_sent"
        return

    # etap 2: po opisie pracy, teraz startujemy pytania
    if state == "job_sent":
        if any(w in text for w in NEGATIVE_KEYWORDS):
            await update.message.reply_text(NEGATIVE_REPLY)
            user_states[uid] = "end"
        elif any(w in text for w in POSITIVE_KEYWORDS):
            # wysyłamy pierwsze pytanie
            await update.message.reply_text(QUESTIONS_LIST[0])
            user_states[uid] = "q_0"
        return

    # etapy 3+: kolejno pytania q_0 ... q_10
    if state.startswith("q_"):
        idx = int(state.split("_")[1])
        # po otrzymaniu odpowiedzi idziemy dalej
        next_idx = idx + 1
        if next_idx < len(QUESTIONS_LIST):
            await update.message.reply_text(QUESTIONS_LIST[next_idx])
            user_states[uid] = f"q_{next_idx}"
        else:
            # wszystkie pytania zadane → final
            await update.message.reply_text(FINAL_REPLY)
            user_states[uid] = "end"
        return

    # koniec
    # (jeśli state == "end", nic nie robimy)
    return

if __name__ == "__main__":
    # usuń stary webhook, żeby Telegram pozwolił na polling
    tmp_app = ApplicationBuilder().token(TOKEN).build()
    tmp_app.bot.delete_webhook()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 RekrutacjaSharryBot: polling uruchomiony.")
    app.run_polling()
