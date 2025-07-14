from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 🔐 Token do bota Telegram
TOKEN = "8149438916:AAERXz-gzOy8aPOhBQVCU88Q8EMe_6WMuZs"

# 🔐 Autoryzacja do Google Sheets – NOWE SCOPES
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
import os

# Zapisz sekret do pliku tymczasowego (Render pozwala odczytać z ENV)
with open("temp_credentials.json", "w") as f:
    f.write(os.environ["GOOGLE_CREDENTIALS"])

credentials = ServiceAccountCredentials.from_json_keyfile_name("temp_credentials.json", scope)
client = gspread.authorize(credentials)
sheet = client.open("RekrutacjaSharryBot").sheet1  # nazwa arkusza Google

# 🔍 Słowa kluczowe
NEGATIVE_KEYWORDS = ["ні", "нет", "нецікаво", "ni", "net", "no"]
POSITIVE_KEYWORDS = ["так", "да", "цікаво", "tak", "da", "yes"]

# 📌 Stany użytkowników
user_states = {}

# 📩 Wiadomości
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
Самостійно шукати пасажирів Вам НЕ потрібно, ми так не працюємо, пасажири самі приходять на наш сайт. Також важливо, що для роботи необхідний власний комп'ютер, з телефону працювати не можна.!

Робота включатиме:
-Обробку замовлень, які надходять на наш сайт, де пасажири бронюють квитки на автобуси та буси.
-Зв'язок із пасажирами для підтвердження їх замовлень у системі.
-Інформування пасажирів про умови рейсу.
-Надсилання електронних квитків пасажирам.
-Робота з панеллю резервування в кабінеті диспетчера.
-Обслуговування інфолінії.

Чи буде це для вас цікаво?"""

QUESTIONS = """Чудово! 😊 Тоді пропоную трохи ближче познайомитись. Розкажіть, будь ласка, кілька слів про себе, а також дайте відповіді на короткі запитання нижче — і ми домовимось про телефонну розмову:

- Звідки Ви? (місто)
- Ваш вік
- Освіта (спеціальність)
Ваш досвід роботи:
- Чи мали Ви досвід віддаленої роботи?
- Чи працювали з CRM-системами?
- Чи мали досвід з телефонією або кол-центрами (дзвінки, IP-телефонія)?
- Чи маєте  доступ до комп’ютера/ноутбуку та стабільного інтернету?  (робота з телефону неможлива!)
- Скільки годин можете приділяти роботі?
- В який час (день/вечір/ніч) Вам зручніше працювати?
- Номер телефону, за яким наш співробітник може зателефонувати, щоб обговорити деталі."""

FINAL_REPLY = """Дякуємо за ваші відповіді. Ви дуже цікавий кандидат :)
Якщо ви хочете отримати доступ до навчальних матеріалів, щоб краще зрозуміти, чи підходить вам ця робота, така можливість є. Для цього необхідно підписати угоду про конфіденційність. Якщо ви зацікавлені, надішліть відповідний запит на адресу hr@sharry.eu."""

# 🟨 Zapis odpowiedzi do arkusza Google
def log_user_response(user_id, username, text):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([now, str(user_id), username or "-", text])

# 🔹 Komenda /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = "initial"
    await update.message.reply_text(INITIAL_MESSAGE)

# 🔹 Obsługa wiadomości
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()
    username = update.effective_user.username

    log_user_response(user_id, username, text)
    state = user_states.get(user_id, "initial")

    if state == "initial":
        if any(w in text for w in NEGATIVE_KEYWORDS):
            await update.message.reply_text(NEGATIVE_REPLY)
            user_states[user_id] = "end"
        elif any(w in text for w in POSITIVE_KEYWORDS):
            await update.message.reply_text(JOB_DESCRIPTION)
            user_states[user_id] = "job_sent"
        return

    if state == "job_sent":
        if any(w in text for w in NEGATIVE_KEYWORDS):
            await update.message.reply_text(NEGATIVE_REPLY)
            user_states[user_id] = "end"
        elif any(w in text for w in POSITIVE_KEYWORDS):
            await update.message.reply_text(QUESTIONS)
            user_states[user_id] = "questions_sent"
        return

    if state == "questions_sent":
        await update.message.reply_text(FINAL_REPLY)
        user_states[user_id] = "end"
        return

# 🔹 Uruchomienie bota
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 RekrutacjaSharryBot działa...")
    app.run_polling()
