import os
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 BFSG-Checker von Michael Tribis\n\nSchick mir eine URL — ich prüfe sie sofort.\n\nBeispiel: bernhard-burger.de"
    )

async def check_website(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = update.message.text.strip()
    if not raw.startswith("http"):
        url = "https://" + raw
    else:
        url = raw

    await update.message.reply_text("⏳ Prüfe Website...")

    try:
        params = {"url": url, "category": "accessibility", "strategy": "mobile", "locale": "de"}
        response = requests.get("https://www.googleapis.com/pagespeedonline/v5/runPagespeed", params=params, timeout=40)
        data = response.json()

        if "error" in data:
            await update.message.reply_text("❌ Website nicht erreichbar.")
            return

        score = round(data["lighthouseResult"]["categories"]["accessibility"]["score"] * 100)
        audits = data["lighthouseResult"]["audits"]

        if score >= 90:
            emoji = "🟢"
            status = "Gut — kein Handlungsbedarf"
            empfehlung = "Dieser Kunde braucht uns nicht."
        elif score >= 60:
            emoji = "🟡"
            status = "Verbesserungsbedarf — möglicher Kunde"
            empfehlung = "Anschreiben lohnt sich."
        else:
            emoji = "🔴"
            status = "KRITISCH — sofort ansprechen"
            empfehlung = "Das ist unser Kunde. Jetzt kontaktieren."

        issue_map = {
            "image-alt": "Bilder ohne Alt-Text",
            "color-contrast": "Zu geringer Farbkontrast",
            "label": "Formularfelder ohne Label",
            "document-title": "Seitentitel fehlt",
            "html-has-lang": "Sprache nicht gesetzt",
            "heading-order": "Falsche Überschriften-Reihenfolge",
            "link-name": "Links ohne Beschriftung",
        }

        issues = []
        for key, label in issue_map.items():
            audit = audits.get(key, {})
            if audit.get("score") == 0:
                items = audit.get("details", {}).get("items", [])
                count = f" ({len(items)}x)" if items else ""
                issues.append(f"• {label}{count}")

        issues_text = "\n".join(issues[:6]) if issues else "Keine kritischen Verstöße"

        msg = (
            f"{emoji} *{status}*\n"
            f"Score: *{score}/100*\n"
            f"Website: {raw}\n\n"
            f"*Verstöße:*\n{issues_text}\n\n"
            f"💡 _{empfehlung}_"
        )

        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Fehler: {str(e)}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_website))
    print("Bot läuft...")
    app.run_polling()

if __name__ == "__main__":
    main()
