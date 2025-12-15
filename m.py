import os
import shutil
import zipfile
import patoolib
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

API_ID = "21303916"
API_HASH = "a95f38df3dc1f71b6497798a40b993ab"
BOT_TOKEN = "7999993306:AAErliPYDEwJXKZhkMCw9JtPedQAh-KAZGc"
LOG_GROUP_ID = "-5014285223"

DOWNLOAD_DIR = "downloads"
EXTRACT_DIR = "extracted"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(EXTRACT_DIR, exist_ok=True)

app = Client(
    "ubzip",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# user_id : (archive_path, original_filename, archive_type)
user_files = {}


# ───────────── ZIP PASSWORD DETECTION ─────────────
def zip_needs_password(zip_path):
    try:
        with zipfile.ZipFile(zip_path) as z:
            for info in z.infolist():
                if info.flag_bits & 0x1:
                    return True
        return False
    except:
        return True


# ───────────── START ─────────────
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply(
        "👋 **UBZIP BOT**\n\n"
        "📦 Supports ALL password types:\n"
        "• ZIP / RAR / 7Z\n"
        "• Normal & encrypted\n\n"
        "🛠 Send archive → send password if asked",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("ℹ️ Help", callback_data="help")]]
        )
    )


@app.on_callback_query(filters.regex("help"))
async def help_cb(client, cb):
    await cb.message.edit(
        "📘 **How to use**\n\n"
        "1️⃣ Send ZIP / RAR / 7Z\n"
        "2️⃣ If password required → send it\n"
        "3️⃣ Files will be extracted\n\n"
        "⚠️ Wrong password = extraction fails"
    )


# ───────────── FILE HANDLER ─────────────
@app.on_message(filters.document & filters.private)
async def file_handler(client, message: Message):
    filename = message.document.file_name
    lower = filename.lower()

    if not lower.endswith(("zip", "rar", "7z")):
        return

    status = await message.reply("📥 Downloading...")
    archive_path = await message.download(DOWNLOAD_DIR)

    # ZIP without password → auto extract
    if lower.endswith(".zip") and not zip_needs_password(archive_path):
        await extract_and_send(
            client,
            message,
            archive_path,
            filename,
            password=None,
            archive_type="zip"
        )
        return

    # Password required
    archive_type = "zip" if lower.endswith(".zip") else "rar7z"
    user_files[message.from_user.id] = (archive_path, filename, archive_type)

    await status.edit("🔐 Archive is password protected.\nSend password now.")


# ───────────── PASSWORD HANDLER ─────────────
@app.on_message(filters.text & filters.private)
async def password_handler(client, message: Message):
    uid = message.from_user.id

    if uid not in user_files:
        return

    archive_path, filename, archive_type = user_files[uid]
    password = message.text  # DO NOT STRIP (supports spaces & special chars)

    await extract_and_send(
        client,
        message,
        archive_path,
        filename,
        password=password,
        archive_type=archive_type
    )


# ───────────── EXTRACT & SEND ─────────────
async def extract_and_send(client, message, archive, original_name, password, archive_type):
    uid = message.from_user.id
    extract_path = os.path.join(EXTRACT_DIR, str(uid))
    os.makedirs(extract_path, exist_ok=True)

    status = await message.reply("📂 Extracting...")

    try:
        if archive_type == "zip":
            with zipfile.ZipFile(archive) as z:
                if password:
                    z.extractall(extract_path, pwd=password.encode())
                else:
                    z.extractall(extract_path)

        else:
            patoolib.extract_archive(
                archive,
                outdir=extract_path,
                password=password,
                interactive=False
            )

        await status.edit("📤 Sending files...")
        for root, _, files in os.walk(extract_path):
            for f in files:
                await message.reply_document(os.path.join(root, f))

        await client.send_message(
            LOG_GROUP_ID,
            f"✅ Extracted\n"
            f"👤 User: {uid}\n"
            f"📦 File: {original_name}"
        )

    except Exception:
        await status.edit("❌ Wrong password or unsupported encryption")

    finally:
        shutil.rmtree(extract_path, ignore_errors=True)
        if os.path.exists(archive):
            os.remove(archive)
        user_files.pop(uid, None)


app.run()
