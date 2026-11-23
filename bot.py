import json
import os
import uuid
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ==========================================
# এখানে আপনার BotFather থেকে পাওয়া Token বসান:
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# '@' ছাড়া আপনার বটের ইউজারনেম বসান (ঐচ্ছিক, খালি রাখলে বট নিজেই নিয়ে নেবে):
BOT_USERNAME = ""  # যেমন: "MyFileShare_bot"
# ==========================================

DATA_FILE = "shared_items.json"


def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_data(data: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_token() -> str:
    token = BOT_TOKEN.strip()
    if not token or token == "YOUR_BOT_TOKEN_HERE":
        token = input("আপনার Bot Token দিন: ").strip()
    return token


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    if args:
        code = args[0]
        data = load_data()
        item = data.get(code)

        if not item:
            await update.message.reply_text("❌ দুঃখিত, এই লিঙ্কটি সঠিক নয় বা পাওয়া যায়নি।")
            return

        item_type = item["type"]
        content = item["content"]
        caption = item.get("caption") or ""

        if item_type == "video":
            await update.message.reply_video(video=content, caption=caption)
        elif item_type == "document":
            await update.message.reply_document(document=content, caption=caption)
        elif item_type == "photo":
            await update.message.reply_photo(photo=content, caption=caption)
        elif item_type == "audio":
            await update.message.reply_audio(audio=content, caption=caption)
        elif item_type == "text":
            await update.message.reply_text(content)
        return

    await update.message.reply_text(
        "👋 স্বাগতম!\n\n"
        "যেকোনো **ভিডিও, ফাইল, ছবি, অডিও বা টেক্সট** পাঠান — "
        "আমি আপনাকে একটি **Deep Link** তৈরি করে দেবো।"
    )


async def handle_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    item_type = None
    content = None
    caption = msg.caption

    if msg.video:
        item_type = "video"
        content = msg.video.file_id
    elif msg.document:
        item_type = "document"
        content = msg.document.file_id
    elif msg.photo:
        item_type = "photo"
        content = msg.photo[-1].file_id
    elif msg.audio:
        item_type = "audio"
        content = msg.audio.file_id
    elif msg.text and not msg.text.startswith("/"):
        item_type = "text"
        content = msg.text

    if not item_type:
        await msg.reply_text("⚠️ এই ধরনের কনটেন্ট সাপোর্ট করে না।")
        return

    code = uuid.uuid4().hex[:8]
    data = load_data()
    data[code] = {
        "type": item_type,
        "content": content,
        "caption": caption,
    }
    save_data(data)

    username = BOT_USERNAME.strip().lstrip("@")
    if not username:
        bot_info = await context.bot.get_me()
        username = bot_info.username

    deep_link = f"https://t.me/{username}?start={code}"

    await msg.reply_text(
        f"✅ ডিপ লিঙ্ক তৈরি হয়েছে!\n\n"
        f"🔗 লিঙ্ক: `{deep_link}`",
        parse_mode="Markdown",
    )


if __name__ == "__main__":
    token = get_token()
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(
            filters.VIDEO
            | filters.Document.ALL
            | filters.PHOTO
            | filters.AUDIO
            | (filters.TEXT & ~filters.COMMAND),
            handle_content,
        )
    )
    print("Bot is running...")
    app.run_polling()
          
