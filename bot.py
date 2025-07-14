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
TOKEN = os.environ["TELEGRAM_TOKEN"]  # ustaw w Render: Environment → TELEGRAM_TOKEN

# ── GOOGLE SHEETS ───────────────────────────────────────────────────────────
GOOGLE_SECRET_FILE = "/etc/secrets/GOOGLE_CREDENTIALS"  # Secret Files → GOOGLE_CREDENTIALS
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

# Sesje trzymają stan rozmowy: 'stage' i, ewentualnie, 'q_index' dla pytań
user_sessions = {}

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
Ваша основна роль буде полягати в опрацюванні вхідних запитів, дзвінків та повідомлень...
(pełny tekst opisu — wklej swój)
Чи буде це для вас цікаво?
"""

# lista pojedynczych pytań
QUESTIONS_LIST = [
    "1️⃣ Звідки Ви? (місто)",
    "2️⃣ Ваш вік",
    "3️⃣ Освіта (спеціальність)",
    "4️⃣ Ваш досвід роботи",
    "5️⃣ Чи мали Ви досвід віддаленої роботи? (так/ні)",
    "6️⃣ Чи працювали з CRM-системами? (так/ні)",
    "7️⃣ Чи мали досвід з телефонією або кол-центрами? (так/ні)",
    "8️⃣ Чи маєте доступ до комп’ютера/ноутбуку та стабільного інтернету?",
    "9️⃣ Скільки годин можете приділяти роботі на добу?",
    "🔟 В який час (день/вечір/ніч) Вам зручніше працювати?",
    "1️⃣1️⃣ Номер телефону, за яким ми можемо зателефонувати:"
]

FINAL_REPLY = """\
Дякуємо за ваші відповіді! 🎉
Якщо ви хочете отримати доступ до навчальних матеріалів, будь ласка, надішліть запит на hr@sharry.eu.
"""

def log_user_response(user_id: int, username: str, text: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, str(user_id), username or "-", text])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    # inicjalizacja sesji
    user_sessions[uid] = {"stage": "initial"}
    await update.message.reply_text(INITIAL_MESSAGE)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip().lower()
    username = update.effective_user.username or "-"
    log_user_response(uid, username, update.message.text)

    sess = user_sessions.get(uid)
    if not sess:
        # ktoś pisze bez /start
        user_sessions[uid] = {"stage": "initial"}
        await update.message.reply_text("Proszę rozpocząć od /start")
        return

    stage = sess["stage"]

    # etap wstępny
    if stage == "initial":
        if any(w in text for w in NEGATIVE_KEYWORDS):
            await update.message.reply_text(NEGATIVE_REPLY)
            sess["stage"] = "end"
        elif any(w in text for w in POSITIVE_KEYWORDS):
            await update.message.reply_text(JOB_DESCRIPTION)
            sess["stage"] = "job_sent"
        else:
            # nie rozumiemy, pytamy jeszcze raz
            await update.message.reply_text("Proszę odpowiedzieć tak/нет/ні/net/no")
        return

    # etap opisu pracy
    if stage == "job_sent":
        if any(w in text for w in NEGATIVE_KEYWORDS):
            await update.message.reply_text(NEGATIVE_REPLY)
            sess["stage"] = "end"
        elif any(w in text for w in POSITIVE_KEYWORDS):
            # przechodzimy do zadawania kolejnych pytań
            sess["stage"] = "asking"
            sess["q_index"] = 0
            await update.message.reply_text(QUESTIONS_LIST[0])
        else:
            await update.message.reply_text("Proszę odpowiedzieć так/нет/ні/net/no")
        return

    # etap zadawania serii pytań
    if stage == "asking":
        idx = sess["q_index"]
        # przechowujemy odpowiedź (opcjonalnie można wrzucić do listy sess["answers"])
        idx += 1
        if idx < len(QUESTIONS_LIST):
            sess["q_index"] = idx
            await update.message.reply_text(QUESTIONS_LIST[idx])
        else:
            # koniec pytań
            await update.message.reply_text(FINAL_REPLY)
            sess["stage"] = "end"
        return

    # jeśli sesja zakończona, ignorujemy dalsze wiadomości
    if stage == "end":
        return

if __name__ == "__main__":
    # usuń ewentualny webhook, by nie kolidował z pollingiem
    tmp = ApplicationBuilder().token(TOKEN).build()
    tmp.bot.delete_webhook()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 RekrutacjaSharryBot: polling uruchomiony.")
    app.run_polling()
