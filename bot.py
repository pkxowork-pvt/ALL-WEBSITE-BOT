import os
import zipfile
import uuid
import asyncio
import threading
from flask import Flask, send_from_directory, abort
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# 1. Bot Token
BOT_TOKEN = "8687941893:AAGNY6S5WTU0skJxlyRCqJbFp3UITtnJl2c"

# 2. Render Public URL
BASE_URL = "https://all-website-bot.onrender.com"

UPLOAD_DIR = os.path.join(os.getcwd(), "hosted_sites")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- FLASK SERVER ---
server = Flask(__name__)

@server.route("/")
def home():
    return "🌐 Website Hosting Server is Live and Running!"

@server.route("/sites/<site_id>/")
@server.route("/sites/<site_id>/<path:filename>")
def serve_site(site_id, filename="index.html"):
    site_path = os.path.join(UPLOAD_DIR, site_id)
    if not os.path.isdir(site_path):
        abort(404)
    return send_from_directory(site_path, filename)

# --- TELEGRAM BOT LOGIC ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Namaste! Mujhe apni website ki `index.html` ya `.zip` file bhejiye, main turant live link bana dunga."
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file_name = doc.file_name.lower()

    if not (file_name.endswith(".html") or file_name.endswith(".zip")):
        await update.message.reply_text("❌ Kripya sirf `.html` ya `.zip` file bhejein!")
        return

    status = await update.message.reply_text("⏳ File process ho rahi hai...")

    site_id = str(uuid.uuid4())[:8]
    target_folder = os.path.join(UPLOAD_DIR, site_id)
    os.makedirs(target_folder, exist_ok=True)

    tg_file = await doc.get_file()

    if file_name.endswith(".html"):
        destination = os.path.join(target_folder, "index.html")
        await tg_file.download_to_drive(destination)
    elif file_name.endswith(".zip"):
        zip_path = os.path.join(target_folder, "site.zip")
        await tg_file.download_to_drive(zip_path)
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(target_folder)
            os.remove(zip_path)
        except Exception:
            await status.edit_text("❌ Invalid ZIP file!")
            return

    live_link = f"{BASE_URL.rstrip('/')}/sites/{site_id}/"
    await status.edit_text(
        f"🎉 **Aapki website live ho chuki hai!**\n\n"
        f"🔗 **Live URL:** {live_link}"
    )

def run_bot():
    # Telegram Bot ko separate thread me chalana
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.run_polling()

if __name__ == "__main__":
    # 1. Telegram bot background thread me shuru hoga
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()

    # 2. Flask server main thread par chalega Render ke assigned PORT ke sath
    port = int(os.environ.get("PORT", 10000))
    server.run(host="0.0.0.0", port=port)
    