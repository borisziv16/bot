import os
import logging
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# שלבים בשיחה
NAME, PHONE, SERVICE, DATE, TIME = range(5)

# הגדרות לוגים
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# משתני סביבה
BOT_TOKEN = os.getenv("BOT_TOKEN")
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
BASE_ID = os.getenv("BASE_ID")
TABLE_NAME = "Appointments"

# פונקציה לשמירה ל-Airtable
def save_to_airtable(data):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"fields": data}
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print("✅ נשלח ל-Airtable בהצלחה")
        print("📄 תשובה:", response.text)
        return True
    except Exception as e:
        print("❌ שגיאה בשליחה ל-Airtable:")
        print(e)
        print("📄 תשובת Airtable:", response.text)
        return False

# שלבי שיחה עם המשתמש
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("שלום! איך קוראים לך?")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("מה מספר הטלפון שלך?")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    services = [["תספורת", "צבע"], ["פן", "תסרוקת"]]
    await update.message.reply_text(
        "איזה שירות אתה רוצה?",
        reply_markup=ReplyKeyboardMarkup(services, one_time_keyboard=True)
    )
    return SERVICE

async def get_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["service"] = update.message.text
    await update.message.reply_text("לאיזה תאריך?")
    return DATE

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["date"] = update.message.text
    await update.message.reply_text("באיזו שעה?")
    return TIME

async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["time"] = update.message.text

    data = {
        "שם": context.user_data["name"],
        "טלפון": context.user_data["phone"],
        "שירות": context.user_data["service"],
        "תאריך": context.user_data["date"],
        "שעה": context.user_data["time"],
    }

    success = save_to_airtable(data)
    if success:
        await update.message.reply_text("ההרשמה בוצעה בהצלחה 🎉")
    else:
        await update.message.reply_text("משהו השתבש בעת ההרשמה 😥")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ביטלת את התהליך. יום נעים!")
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_service)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_time)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
