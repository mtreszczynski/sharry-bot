from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
import datetime
import os

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ── TELEGRAM ────────────────────────────────────────────────────────────────
TOKEN = os.environ["TELEGRAM_TOKEN"]  # ustawione jako Env Var w Render

# ── GOOGLE SHEETS ───────────────────────────────────────────────────────────
# Render montuje Twój Secret File pod /etc/secrets/<Filename>
# Jeśli nazwałeś plik GOOGLE_CREDENTIALS, to ścieżka to właśnie:
GOOGLE_SECRET_FILE = "/etc/secrets/GOOGLE_CREDENTIALS"

# Używamy aktualnych scope'ów dla Sheets i Drive:
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SECRET_FILE, SCOPES)
client = gspread.authorize(creds)
sheet = client.open("RekrutacjaSharryBot").sheet1  # upewnij się, że nazwa arkusza się zgadza

# ── REKRUTACJA ─────────────────────────────────────────────────────────────
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
Ваша основна роль буде полягати в опрацюванні вхідних запитів, дзвінків та повідомлень...
(pełny tekst opisu — wklej swój)
Чи буде це для вас цікаво?
"""

QUESTIONS = """\
Чудово! 😊 Розкажіть кілька слів o собі та дайте відповіді на питання, ...
(pełny zestaw pytań — wklej swój)
"""

FINAL_REPLY = """\
Дякуємо за ваші відповіді. Ви дуже цікавий кандидат :)
Якщо ви хочете доступ до навчальних матеріалів — надішліть запит на hr@sharry.eu
"""

# ── LOGOWANIE DO SHEETS ────────────────────────────────────────────────────
def log_user_response(user_id: int, username: str, text: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, str(user_id), username or "-", text])

# ── HANDLERY ───────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_states[uid] = "initial"
    await update.message.reply_text(INITIAL_MESSAGE)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.lower()
    username = update.effective_user.username or "-"
    
    # Zapisz do Sheets
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

# ── START APLIKACJI ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 RekrutacjaSharryBot działa...")
    app.run_polling()
