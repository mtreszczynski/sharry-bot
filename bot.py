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

# ── 1) TELEGRAM ───────────────────────────────────────────────────────────────
TOKEN = os.environ["TELEGRAM_TOKEN"]  # ustaw w Render > Environment

# ── 2) GOOGLE SHEETS ─────────────────────────────────────────────────────────
# Render montuje Twój Secret File pod /etc/secrets/<Filename>
GOOGLE_SECRET_FILE = "/etc/secrets/GOOGLE_CREDENTIALS"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SECRET_FILE, SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open("RekrutacjaSharryBot").sheet1  # sprawdź nazwę arkusza

# ── 3) REKRUTACJA ────────────────────────────────────────────────────────────
NEGATIVE_KEYWORDS = ["ні", "нет", "нецікаво", "ni", "net", "no"]
POSITIVE_KEYWORDS = ["так", "да", "цікаво", "tak", "da", "yes"]
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
Ваша основна роль буде полягати w op…  # wklej pełny opis
Чи będzie це dla вас цікаво?
"""

QUESTIONS = """\
Чудово! 😊 Далі:
- Z którego miasta jesteś?
- Ile masz lat?
- Wykształcenie?
- Doświadczenie zdalne?
- CRM?
- Telefonia / call-center?
- Dostęp do komputera i internetu?
- Ile godzin dziennie?
- Kiedy możesz pracować?
- Numer kontaktowy?
"""

FINAL_REPLY = """\
Дякуємо за ваші відповіді. Ви дуже цікавий кандидат :)
Aby otrzymać materiały szkoleniowe, wyślij request na hr@sharry.eu
"""

# ── 4) LOGOWANIE DO SHEETS ─────────────────────────────────────────────────
def log_user_response(user_id: int, username: str, text: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([ts, str(user_id), username or "-", text])


# ── 5) HANDLERY ─────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_states[uid] = "initial"
    await update.message.reply_text(INITIAL_MESSAGE)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.lower()
    username = update.effective_user.username or "-"

    # logujemy każdą wiadomość
    log_user_response(uid, username, text)

    state = user_states.get(uid, "initial")

    if state == "initial":
        if any(w in text for w in NEGATIVE_KEYWORDS):
            await update.message.reply_text(NEGATIVE_REPLY)
            user_states[uid] = "end"
        elif any(w in text for w in POSITIVE_KEYWORDS):
            await update.message.reply_text(JOB_DESCRIPTION)
            user_states[uid] = "job_sent"
        return

    if state == "job_sent":
        if any(w in text for w in NEGATIVE_KEYWORDS):
            await update.message.reply_text(NEGATIVE_REPLY)
            user_states[uid] = "end"
        elif any(w in text for w in POSITIVE_KEYWORDS):
            await update.message.reply_text(QUESTIONS)
            user_states[uid] = "questions_sent"
        return

    if state == "questions_sent":
        await update.message.reply_text(FINAL_REPLY)
        user_states[uid] = "end"
        return


# ── 6) START APLIKACJI ───────────────────────────────────────────────────────
if __name__ == "__main__":
    # a) usuwamy stare webhooki, żeby nie było konfliktu z pollingiem
    tmp = ApplicationBuilder().token(TOKEN).build()
    tmp.bot.delete_webhook()

    # b) uruchamiamy polling jedną instancją
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 RekrutacjaSharryBot działa (polling)…")
    app.run_polling()
