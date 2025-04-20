import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, filters,
                          CallbackContext, CallbackQueryHandler, ConversationHandler)

# --- קונסטנטים ---
#AIRTABLE_API_KEY = 'your_airtable_api_key'
#AIRTABLE_BASE_ID = 'your_base_id'
#AIRTABLE_TABLE_NAME = 'Appointments'
AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
#TELEGRAM_TOKEN = 'your_telegram_token'
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_TOKEN")
AIRTABLE_BASE_ID = os.getenv("BASE_ID")
AIRTABLE_TABLE_NAME = "Appointments"

headers = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

# שלבי השיחה
NAME, PHONE, SERVICE, DATE, TIME = range(5)

# שעות קבועות לדוגמה
ALL_HOURS = ["10:00", "11:30", "13:00", "14:30", "16:00"]

# --- התחלה ---
def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("שלום! מה שמך המלא?")
    return NAME

# --- שם ---
def get_name(update: Update, context: CallbackContext) -> int:
    context.user_data["name"] = update.message.text
    update.message.reply_text("מה מספר הטלפון שלך?")
    return PHONE

# --- טלפון ---
def get_phone(update: Update, context: CallbackContext) -> int:
    context.user_data["phone"] = update.message.text
    keyboard = [[InlineKeyboardButton(s, callback_data=s)] for s in ["תספורת", "מניקור", "עיסוי"]]
    update.message.reply_text("בחר שירות:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SERVICE

# --- שירות ---
def get_service(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    context.user_data["service"] = query.data
    query.edit_message_text("הכנס תאריך (בפורמט YYYY-MM-DD):")
    return DATE

# --- תאריך ---
def get_date(update: Update, context: CallbackContext) -> int:
    context.user_data["date"] = update.message.text
    available_hours = get_available_hours(context.user_data["date"])

    if not available_hours:
        update.message.reply_text("אין שעות פנויות ביום זה. נסה תאריך אחר.")
        return DATE

    keyboard = [[InlineKeyboardButton(hour, callback_data=hour)] for hour in available_hours]
    update.message.reply_text("בחר שעה:", reply_markup=InlineKeyboardMarkup(keyboard))
    return TIME

# --- שעה ---
def get_time(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    context.user_data["time"] = query.data

    data = {
        "Name": context.user_data["name"],
        "Telephone": context.user_data["phone"],
        "Service": context.user_data["service"],
        "Date": context.user_data["date"],
        "Time": context.user_data["time"],
    }

    response = requests.post(
        AIRTABLE_URL,
        headers=headers,
        json={"fields": data}
    )

    if response.status_code == 200:
        query.edit_message_text("✅ ההרשמה בוצעה בהצלחה!")
    else:
        query.edit_message_text("❌ משהו השתבש בעת ההרשמה.")
        logging.error("שגיאה בכתיבה ל-Airtable: %s", response.text)

    return ConversationHandler.END

# --- שעות פנויות ---
def get_available_hours(date_str):
    params = {
        "filterByFormula": f"Date='{date_str}'"
    }
    response = requests.get(AIRTABLE_URL, headers=headers, params=params)
    if response.status_code != 200:
        logging.warning("שגיאה בשליפת נתונים מ-Airtable: %s", response.text)
        return ALL_HOURS
    records = response.json().get("records", [])
    taken = [r["fields"].get("Time") for r in records if "Time" in r["fields"]]
    available = [h for h in ALL_HOURS if h not in taken]
    return available

# --- ביטול ---
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("בוטל.")
    return ConversationHandler.END

# --- הפעלת הבוט ---
def main():
    logging.basicConfig(level=logging.INFO)
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.text & ~filters.command, get_name)],
            PHONE: [MessageHandler(filters.text & ~filters.command, get_phone)],
            SERVICE: [CallbackQueryHandler(get_service)],
            DATE: [MessageHandler(filters.text & ~filters.command, get_date)],
            TIME: [CallbackQueryHandler(get_time)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
