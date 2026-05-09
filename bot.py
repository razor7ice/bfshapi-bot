import os
import json
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

TOKEN   = os.environ.get("TELEGRAM_TOKEN", "8427264212:AAGXvFEA7oGO9YCJeXSF6oNLTr8K2-dUBN8")
PSI_KEY = "AIzaSyCXUbeKhjJunanI6cx0oVmxC1_umQeHwp4"
STATS_FILE = "/tmp/bfsg_stats.json"

# ── STATS ─────────────────────────────────────────────────────────────────
def load_stats():
    try:
        with open(STATS_FILE) as f:
            return json.load(f)
    except:
        return {"checks":0,"orders":0,"today_checks":0,"today_orders":0,"date":""}

def save_stats(s):
    try:
        with open(STATS_FILE,"w") as f:
            json.dump(s, f)
    except:
        pass

def inc_stat(key):
    s = load_stats()
    today = str(datetime.now().date())
    if s.get("date") != today:
        s["today_checks"] = 0
        s["today_orders"] = 0
        s["date"] = today
    s[key] = s.get(key, 0) + 1
    if key == "checks":
        s["today_checks"] = s.get("today_checks", 0) + 1
    if key == "orders":
        s["today_orders"] = s.get("today_orders", 0) + 1
    save_stats(s)

# ── COMMANDS ──────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 BFSG-Bot\n\n"
        "Schick mir eine URL — ich prüfe sie sofort.\n\n"
        "📊 /stats — Statistiken\n"
        "Beispiel: obi.de"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = load_stats()
    msg = (
        "📊 *Statistiken — Abmahnrisiko.de*\n\n"
        f"🔍 Prüfungen gesamt: *{s.get('checks', 0)}*\n"
        f"🔍 Heute: *{s.get('today_checks', 0)}*\n\n"
        f"💳 Bestellungen gesamt: *{s.get('orders', 0)}*\n"
        f"💳 Heute: *{s.get('today_orders', 0)}*"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# ── URL CHECK ─────────────────────────────────────────────────────────────
async def check_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = update.message.text.strip()
    u = raw if raw.startswith("http") else "https://" + raw

    await update.message.reply_text("⏳ Prüfe Website...")

    try:
        r = requests.get(
            "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
            params={"url":u,"category":"accessibility","strategy":"desktop","locale":"de","key":PSI_KEY},
            timeout=60
        )
        d = r.json()

        if "error" in d:
            await update.message.reply_text("⚠️ Website nicht erreichbar oder blockiert.")
            return

        score = round(d["lighthouseResult"]["categories"]["accessibility"]["score"] * 100)
        audits = d["lighthouseResult"]["audits"]

        ISSUE_MAP = {
            "image-alt":      "Bilder ohne Alt-Text",
            "color-contrast": "Zu geringer Farbkontrast",
            "label":          "Formularfelder ohne Label",
            "html-has-lang":  "Sprache nicht gesetzt",
            "link-name":      "Links ohne Beschriftung",
            "document-title": "Seitentitel fehlt",
            "heading-order":  "Falsche Überschriften-Reihenfolge",
        }

        CRITICAL = {"image-alt","color-contrast","label","html-has-lang","link-name"}

        issues = []
        has_critical = False
        for key, label in ISSUE_MAP.items():
            a = audits.get(key, {})
            if a.get("score") == 0:
                count = len(a.get("details", {}).get("items", []))
                issues.append(f"• {label} ({count}x)")
                if key in CRITICAL:
                    has_critical = True

        if has_critical:
            emoji = "🔴"
            status = "Abmahnrisiko"
        elif score >= 90:
            emoji = "🟢"
            status = "Konform"
        else:
            emoji = "🟡"
            status = "Verbesserungsbedarf"

        issues_text = "\n".join(issues[:6]) if issues else "Keine kritischen Fehler"

        msg = (
            f"{emoji} *{status}*\n"
            f"Score: *{score}/100*\n"
            f"URL: {raw}\n\n"
            f"*Verstöße:*\n{issues_text}"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    except requests.exceptions.Timeout:
        await update.message.reply_text("⏱ Timeout — Website zu langsam.")
    except Exception as e:
        await update.message.reply_text(f"❌ Fehler: {str(e)}")

# ── MAIN ──────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_url))
    print("Bot läuft...")
    app.run_polling()

if __name__ == "__main__":
    main()
