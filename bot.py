import os
import zipfile
import uuid
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

# 1. Apna Telegram Bot Token yahan daalein
BOT_TOKEN = "8687941893:AAGNY6S5WTU0skJxlyRCqJbFp3UITtnJl2c"

# 2. Render service ka public URL (Render dashboard se copy karein, e.g., 'https://my-service.onrender.com')
BASE_URL = "https://youtube-instagram-download.onrender.com"

UPLOAD_DIR = "hosted_sites"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- FLASK WEB SERVER (Website files serve karne ke liye) ---
server = Flask(__name__)

@server.route("/")
def home():
    return "🌐 Telegram Hosting Bot Server is Running!"

@server.route("/sites/<site_id>/")
@server.route("/sites/<site_id>/<path:filename>")
def serve_site(site_id, filename="index.html"):
    site_path = os.path.join(UPLOAD_DIR, site_id)
    if not os.path.exists(site_path):
        abort(404)
    return send_from_directory(site_path, filename)

def run_flask():
    # Render default port 10000 use karta hai
    port = int(os.environ.get("PORT", 10000))
    server.run(host="0.0.0.0", port=port)

# --- TELEGRAM BOT LOGIC ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Namaste! Main Website Hosting Bot hoon.**\n\n"
        "Aap mujhe apni website ki file bhejiye:\n"
        "• Single `index.html` file\n"
        "• Ya full website ka `.zip` folder (jisme `index.html`, css, images hon)\n\n"
        "Main turant aapko free live link generate karke dunga!"
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file_name = doc.file_name.lower()

    if not (file_name.endswith(".html") or file_name.endswith(".zip")):
        await update.message.reply_text("❌ Kripya sirf `.html` ya `.zip` file bhejein!")
        return

    status = await update.message.reply_text("⏳ File download aur host ho rahi hai...")

    site_id = str(uuid.uuid4())[:8]
    target_folder = os.path.join(UPLOAD_DIR, site_id)
    os.makedirs(target_folder, exist_ok=True)

    # Telegram se file fetch karna
    tg_file = await doc.get_file()

    if file_name.endswith(".html"):
        destination = os.path.join(target_folder, "index.html")
        await tg_file.download_to_drive(destination)
    elif file_name.endswith(".zip"):
        zip_path = os.path.join(target_folder, "site.zip")
        await tg_file.download_to_drive(zip_path)
        
        # Zip extract karna
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(target_folder)
            os.remove(zip_path)
        except Exception as e:
            await status.edit_text("❌ Corrupted ZIP file!")
            return

    live_link = f"{BASE_URL.rstrip('/')}/sites/{site_id}/"
    await status.edit_text(
        f"🎉 **Aapki website live ho chuki hai!**\n\n"
        f"🔗 **Live URL:** {live_link}\n\n"
        f"Kisi bhi browser me khol kar check karein."
    )

def main():
    # Flask server ko alag thread me start karna
    threading.Thread(target=run_flask, daemon=True).start()

    # Telegram bot start karna
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("Hosting Bot Active!")
    app.run_polling()

if __name__ == "__main__":
    main()
    