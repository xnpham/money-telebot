from typing import Final
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
from zoneinfo import ZoneInfo  # Add this import at the top
from pymongo import MongoClient
from bson import ObjectId

# load_dotenv()
TOKEN: Final = os.getenv('TOKEN')
BOT_USERNAME: Final = os.getenv('BOT_USERNAME')
MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('DB_NAME')
COLLECTION_NAME = os.getenv('COLLECTION_NAME')

# Financial data structure
finance_data = {
    'balance': 0,
    'monthly_spending': 0,
    'last_month': datetime.now().month,
    'user_chat_id': None,  # To store the user's chat ID for daily reports
    'daily_data': {}  # Stores daily income and expenses
}

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
OBJECTID = ObjectId(os.getenv('OBJECT_ID_STRING'))  # Replace with your actual ObjectId

# Load/save financial data
def load_data():
    global finance_data
    doc = collection.find_one({"_id": OBJECTID})
    if doc:
        finance_data.update({k: v for k, v in doc.items() if k != "_id"})
    else:
        save_data()  # Lưu dữ liệu mặc định nếu chưa có

def save_data():
    collection.update_one(
        {"_id": OBJECTID},
        {"$set": finance_data},
        upsert=True
    )

def check_new_month():
    current_month = datetime.now().month
    if current_month != finance_data.get('last_month'):
        finance_data['monthly_spending'] = 0
        finance_data['last_month'] = current_month
        save_data()

# Helper to update daily data
def update_daily_data(date_key, thu=0, chi=0):
    if date_key not in finance_data['daily_data']:
        finance_data['daily_data'][date_key] = {'thu': 0, 'chi': 0}
    finance_data['daily_data'][date_key]['thu'] += thu
    finance_data['daily_data'][date_key]['chi'] += chi

# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! I am spd1810_bot. How can I assist you today?')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
    Available commands:
    /start - Start the bot
    /help - Show this help message
    /custom - Custom command
    /chi <amount> - Record an expense
    /thu <amount> - Record income
    /remove - Remove all data
    /check - Check current balance
    /yest - Show yesterday's income and expenses
    """
    await update.message.reply_text(help_text)

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('This is a custom command')

# New financial commands
async def chi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    check_new_month()

    # Store user chat ID for daily notifications
    finance_data['user_chat_id'] = update.effective_chat.id

    # Get the amount from command arguments
    if not context.args:
        await update.message.reply_text('Please provide an amount. Usage: /chi <amount>')
        return

    try:
        amount = float(context.args[0])
    except ValueError:
        await update.message.reply_text('Please provide a valid number.')
        return

    # Update financial data
    finance_data['monthly_spending'] += amount
    finance_data['balance'] -= amount

    # Update daily data
    date_key = datetime.now().strftime('%Y-%m-%d')
    update_daily_data(date_key, chi=amount)

    save_data()

    # Respond with current status
    response = f"Recorded expense: {amount}\nCurrent balance: {finance_data['balance']}\nTotal spent this month: {finance_data['monthly_spending']}"
    await update.message.reply_text(response)

async def thu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    check_new_month()

    # Store user chat ID for daily notifications
    finance_data['user_chat_id'] = update.effective_chat.id

    # Get the amount from command arguments
    if not context.args:
        await update.message.reply_text('Please provide an amount. Usage: /thu <amount>')
        return

    try:
        amount = float(context.args[0])
    except ValueError:
        await update.message.reply_text('Please provide a valid number.')
        return

    # Update financial data
    finance_data['balance'] += amount

    # Update daily data
    date_key = datetime.now().strftime('%Y-%m-%d')
    update_daily_data(date_key, thu=amount)

    save_data()

    # Respond with current status
    response = f"Recorded income: {amount}\nCurrent balance: {finance_data['balance']}\nTotal spent this month: {finance_data['monthly_spending']}"
    await update.message.reply_text(response)

# Yesterday's summary
async def yest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    yesterday_key = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    yesterday_data = finance_data['daily_data'].get(yesterday_key, {'thu': 0, 'chi': 0})

    response = (f"Yesterday's summary:\n"
                f"Income (thu): {yesterday_data['thu']}\n"
                f"Expenses (chi): {yesterday_data['chi']}")
    await update.message.reply_text(response)

# Daily notification
async def send_daily_report(context: ContextTypes.DEFAULT_TYPE):
    check_new_month()

    if finance_data.get('user_chat_id'):
        message = f"Daily financial report:\nCurrent balance: {finance_data['balance']}\nTotal spent this month: {finance_data['monthly_spending']}"
        await context.bot.send_message(chat_id=finance_data['user_chat_id'], text=message)

# Remove data
async def remove_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    finance_data.clear()
    save_data()
    await update.message.reply_text('All data has been removed.')

# Check balance
async def check_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    check_new_month()

    # Store user chat ID for daily notifications
    finance_data['user_chat_id'] = update.effective_chat.id

    # Respond with current balance
    response = f"Current balance: {finance_data['balance']}"
    await update.message.reply_text(response)

# Responses
async def handle_response(text: str) -> str:
    process: str = text.lower()
    if 'hello' in process:
        return 'Hello! How can I help you?'
    elif 'bye' in process:
        return 'Goodbye! Have a great day!'
    else:
        return 'I am not sure how to respond to that.'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')

    if message_type == 'group':
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = await handle_response(new_text)
        else:
            return
    else:
        response: str = await handle_response(text)

    print(f'Bot ({update.message.chat.id}): "{response}"')
    await update.message.reply_text(response)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update "{update}" caused error "{context.error}"')

if __name__ == '__main__':
    print('Starting bot...')
    load_data()  # Load existing finance data

    application = ApplicationBuilder().token(TOKEN).build()

    # Commands
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('custom', custom_command))
    application.add_handler(CommandHandler('chi', chi_command))
    application.add_handler(CommandHandler('thu', thu_command))
    application.add_handler(CommandHandler('remove', remove_data))
    application.add_handler(CommandHandler('check', check_balance))
    application.add_handler(CommandHandler('yest', yest_command))

    # Messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Error handler
    application.add_error_handler(error)

    # Schedule daily report at 6 AM Vietnam time
    job_queue = application.job_queue
    vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
    now_vn = datetime.now(vn_tz)
    target_time = now_vn.replace(hour=6, minute=0, second=0, microsecond=0)
    if now_vn > target_time:
        target_time = target_time + timedelta(days=1)  # Schedule for tomorrow if it's already past 6AM

    initial_delay = (target_time - now_vn).total_seconds()
    job_queue.run_repeating(send_daily_report, interval=86400, first=initial_delay)  # 86400 seconds = 24 hours

    # Start the bot
    print('Polling...')
    application.run_polling(poll_interval=3.0)