import os
import requests
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN   = os.environ.get("TELEGRAM_TOKEN", "8427264212:AAGXvFEA7oGO9YCJeXSF6oNLTr8K2-dUBN8")
CHAT_ID = "731884877"

def count_messages():
    """Count messages in chat using getUpdates history"""
    checks = 0
    orders = 0
    today_checks = 0
    today_orders = 0
    today = datetime.now(timezone.utc).date()

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        params = {"limit": 100, "offset": -100}
        r = requests.get(url, params=params, timeout=10)
        updates = r.json().get("result", [])

        for u in updates:
            msg = u.get("message", {})
            text = msg.get("text", "")
            date = msg.get("date", 0)
            msg_date = datetime.fromtimestamp(date, tz=timezone.utc).date()

            if "BESTELLUNG" in text:
                orders += 1
                if msg_date == today:
                    today_orders += 1
            elif any(x in text for x in ["ABMAHNRISIKO", "Verbesserungsbedarf", "Konform"]):
                checks += 1
                if msg_date == today:
                    today_checks += 1

    except Exception as e:
        print(f"Error: {e}")

    return checks, orders, today_checks, today_orders

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 BFSG Stats Bot\n\n"
        "/stats — Statistiken anzeigen"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Zähle...")
    checks, orders, today_c, today_o = count_messages()
    await update.message.reply_text(
        "📊 *Abmahnrisiko.de — Statistiken*\n\n"
        f"🔍 Prüfungen gesamt: *{checks}*\n"
        f"🔍 Heute: *{today_c}*\n\n"
        f"💳 Bestellungen gesamt: *{orders}*\n"
        f"💳 Heute: *{today_o}*",
        parse_mode="Markdown"
    )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    print("Bot läuft...")
    app.run_polling()

if __name__ == "__main__":
    main()
