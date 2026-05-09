import os
import requests
from datetime import datetime, timezone, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN   = os.environ.get("TELEGRAM_TOKEN", "8427264212:AAGXvFEA7oGO9YCJeXSF6oNLTr8K2-dUBN8")
CHAT_ID = "731884877"

KEYBOARD = ReplyKeyboardMarkup(
    [[KeyboardButton("📊 Heute"), KeyboardButton("📅 Woche"), KeyboardButton("🗓 Monat")]],
    resize_keyboard=True,
    persistent=True
)

def get_stats(days):
    checks = 0
    orders = 0
    since  = datetime.now(timezone.utc) - timedelta(days=days)

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        r   = requests.get(url, params={"limit":100,"offset":-100}, timeout=10)
        for u in r.json().get("result", []):
            msg  = u.get("message", {})
            text = msg.get("text", "")
            ts   = datetime.fromtimestamp(msg.get("date", 0), tz=timezone.utc)
            if ts < since:
                continue
            if "BESTELLUNG" in text:
                orders += 1
            elif any(x in text for x in ["ABMAHNRISIKO","Verbesserungsbedarf","Konform"]):
                checks += 1
    except Exception as e:
        print(e)

    return checks, orders

def format_stats(label, days):
    checks, orders = get_stats(days)
    return (
        f"📊 *{label}*\n\n"
        f"🔍 Prüfungen: *{checks}*\n"
        f"💳 Bestellungen: *{orders}*"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 BFSG Stats Bot\n\nWähle einen Zeitraum:",
        reply_markup=KEYBOARD
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    if "Heute" in text:
        msg = format_stats("Heute", 1)
    elif "Woche" in text:
        msg = format_stats("Diese Woche", 7)
    elif "Monat" in text:
        msg = format_stats("Dieser Monat", 30)
    else:
        return
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=KEYBOARD)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("Bot läuft...")
    app.run_polling()

if __name__ == "__main__":
    main()
