import logging
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

# ========== הגדרות Airtable ==========
AIRTABLE_TOKEN = 'q'
BASE_ID = 's'
TABLE_NAME = 'Orders_recodring'

# ========== טוקן בוט טלגרם ==========
BOT_TOKEN = 'd'

# ========== מצבים ==========
NAME, PHONE, SERVICE, DATE, TIME = range(5)

# ========== הפעלת לוג ==========
logging.basicConfig(level=logging.INFO)

# ========== פונקציית Airtable ==========
def save_to_airtable(name, phone, service, date, time):
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}'
    headers = {
        'Authorization': f'Bearer {AIRTABLE_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        "fields": {
            "Name": name,
            "Telephone": phone,
            "Service": service,
            "Date": date,
            "Time": time
        }
    }
    r = requests.post(url, json=data, headers=headers)
    return r.status_code == 200

# ========== Handlers ==========
def start(update: Update, context: CallbackContext):
    update.message.reply_text("שלום! איך קוראים לך?")
    return NAME

def get_name(update: Update, context: CallbackContext):
    context.user_data['name'] = update.message.text
    update.message.reply_text("מה מספר הטלפון שלך?")
    return PHONE

def get_phone(update: Update, context: CallbackContext):
    context.user_data['phone'] = update.message.text
    reply_keyboard = [['תספורת', 'מניקור', 'פדיקור']]
    update.message.reply_text("איזה שירות תרצה?", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return SERVICE

def get_service(update: Update, context: CallbackContext):
    context.user_data['service'] = update.message.text
    update.message.reply_text("באיזה תאריך? (לדוגמה: 2025-04-25)")
    return DATE

def get_date(update: Update, context: CallbackContext):
    context.user_data['date'] = update.message.text
    update.message.reply_text("באיזו שעה? (לדוגמה: 14:30)")
    return TIME

def get_time(update: Update, context: CallbackContext):
    context.user_data['time'] = update.message.text
    data = context.user_data

    success = save_to_airtable(data['name'], data['phone'], data['service'], data['date'], data['time'])

    if success:
        update.message.reply_text("ההזמנה נרשמה בהצלחה! ניצור איתך קשר 😊")
    else:
        update.message.reply_text("משהו השתבש בעת ההרשמה 😕 נסה שוב")

    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("ביטול ההרשמה.")
    return ConversationHandler.END

# ========== Main ==========
def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)],
            PHONE: [MessageHandler(Filters.text & ~Filters.command, get_phone)],
            SERVICE: [MessageHandler(Filters.text & ~Filters.command, get_service)],
            DATE: [MessageHandler(Filters.text & ~Filters.command, get_date)],
            TIME: [MessageHandler(Filters.text & ~Filters.command, get_time)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
