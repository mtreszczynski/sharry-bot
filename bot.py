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
TOKEN = os.environ.get("TELEGRAM_TOKEN")  # ustaw w Render: Environment → TELEGRAM_TOKEN

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
sessions = {}

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

# Cały blok pytań zapisany jako multiline, ale podzielimy go na 11 oddzielnych
QUESTIONS = """\
1. Звідки Ви? (місто)
2. Ваш вік
3. Освіта (спеціальність)
4. Ваш досвід роботи:
5. Чи мали Ви досвід віддаленої роботи?
6. Чи працювали з CRM-системами?
7. Чи мали досвід з телефонією або кол-центрами (дзвінки, IP-телефонія)?
8. Чи маєте  доступ до комп’ютера/ноутбуку та стабільного інтернету?  (робота з телефону неможлива!)
9. Скільки годин можете приділяти роботі?
10. В який час (день/вечір/ніч) Вам зручніше працювати?
11. Номер телефону, за яким наш співробітник може зателефонувати, щоб обговорити деталі.
"""

FINAL_REPLY = """\
Дякуємо за ваші відповіді. Ви дуже цікавий кандидат
Якщо ви хочете отримати доступ до навчальних матеріалів, щоб краще зрозуміти, чи підходить вам ця робота, така можливість є. Для цього необхідно підписати угоду про конфіденційність. Якщо ви зацікавлені, надішліть відповідний запит на адресу hr@sharry.eu.
"""

# Logowanie do arkusza

def log_user_response(user_id: int, username: str, text: str):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([now, str(user_id), username or "-", text])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    sessions[uid] = {"stage": "initial"}
    await update.message.reply_text(INITIAL_MESSAGE)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    lower_text = text.lower()
    username = update.message.from_user.username or "-"
    log_user_response(uid, username, text)

    sess = sessions.get(uid)
    if not sess:
        return await update.message.reply_text("Proszę zacząć od /start")

    stage = sess["stage"]

    if stage == "initial":
        if any(w in lower_text for w in NEGATIVE_KEYWORDS):
            sess["stage"] = "end"
            return await update.message.reply_text(NEGATIVE_REPLY)
        if any(w in lower_text for w in POSITIVE_KEYWORDS):
            sess["stage"] = "job_sent"
            return await update.message.reply_text(JOB_DESCRIPTION)
        return await update.message.reply_text("Proszę odpowiedzieć tak/ні/net/no")

    if stage == "job_sent":
        if any(w in lower_text for w in NEGATIVE_KEYWORDS):
            sess["stage"] = "end"
            return await update.message.reply_text(NEGATIVE_REPLY)
        if any(w in lower_text for w in POSITIVE_KEYWORDS):
            # dzielimy QUESTIONS na listę 11 pytań
            lines = [q.strip() for q in QUESTIONS.splitlines() if q.strip()]
            sess["stage"] = "asking"
            sess["questions"] = lines
            sess["q_idx"] = 0
            return await update.message.reply_text(lines[0])
        return await update.message.reply_text("Proszę odpowiedzieć tak/ні/net/no")

    if stage == "asking":
        idx = sess["q_idx"] + 1
        questions = sess["questions"]
        if idx < len(questions):
            sess["q_idx"] = idx
            return await update.message.reply_text(questions[idx])
        else:
            sess["stage"] = "end"
            return await update.message.reply_text(FINAL_REPLY)

    # po zakończeniu nic
    return

if __name__ == "__main__":
    # usuwamy stare webhooki
    tmp = ApplicationBuilder().token(TOKEN).build()
    tmp.bot.delete_webhook()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 RekrutacjaSharryBot: polling uruchomiony.")
    app.run_polling()
