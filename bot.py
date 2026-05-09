import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TELEGRAM_TOKEN", "8427264212:AAGXvFEA7oGO9YCJeXSF6oNLTr8K2-dUBN8")
STATS_FILE = "/tmp/bfsg_stats.json"

def load():
    try:
        with open(STATS_FILE) as f:
            return json.load(f)
    except:
        return {"checks":0,"orders":0,"today_checks":0,"today_orders":0,"date":""}

def save(s):
    try:
        with open(STATS_FILE,"w") as f:
            json.dump(s, f)
    except:
        pass

def check_day(s):
    today = str(datetime.now().date())
    if s.get("date") != today:
        s["today_checks"] = 0
        s["today_orders"] = 0
        s["date"] = today
    return s

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 BFSG Stats Bot\n\n"
        "/stats — Statistiken anzeigen\n"
        "/reset — Zurücksetzen"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = check_day(load())
    await update.message.reply_text(
        "📊 *Abmahnrisiko.de*\n\n"
        f"🔍 Prüfungen gesamt: *{s.get('checks',0)}*\n"
        f"🔍 Heute: *{s.get('today_checks',0)}*\n\n"
        f"💳 Bestellungen gesamt: *{s.get('orders',0)}*\n"
        f"💳 Heute: *{s.get('today_orders',0)}*",
        parse_mode="Markdown"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save({"checks":0,"orders":0,"today_checks":0,"today_orders":0,"date":""})
    await update.message.reply_text("✅ Zurückgesetzt.")

async def incoming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    s = check_day(load())
    if "BESTELLUNG" in text:
        s["orders"]       = s.get("orders",0) + 1
        s["today_orders"] = s.get("today_orders",0) + 1
        save(s)
    elif any(x in text for x in ["ABMAHNRISIKO","Verbesserungsbedarf","Konform"]):
        s["checks"]       = s.get("checks",0) + 1
        s["today_checks"] = s.get("today_checks",0) + 1
        save(s)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, incoming))
    print("Bot läuft...")
    app.run_polling()

if __name__ == "__main__":
    main()
