from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import filters
from pyrogram.types import ChatPermissions, Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import RPCError
from datetime import datetime
from . import app, db
from .block import block_dec

# Initialize collection for nightmode
nightmode_collection = db.nightmode

# Chat permissions
LOCK = ChatPermissions(
    can_send_messages=False,
    can_send_media_messages=False,
    can_send_other_messages=False,
    can_send_polls=False,
    can_add_web_page_previews=False
)

UNLOCK = ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=True,
    can_send_other_messages=True,
    can_send_polls=True,
    can_add_web_page_previews=True
)

# Add to group button
button_row = InlineKeyboardMarkup(
    [[InlineKeyboardButton("➕ Add Me To Your Group", url=f"https://t.me/Slave_Grasp_Robot?startgroup=new")]]
)

async def lock_chat(chat_id: int):
    try:
        await app.set_chat_permissions(chat_id, LOCK)
    except Exception as e:
        print(f"Error locking chat {chat_id}: {e}")

async def unlock_chat(chat_id: int):
    try:
        await app.set_chat_permissions(chat_id, UNLOCK)
    except Exception as e:
        print(f"Error unlocking chat {chat_id}: {e}")

@app.on_message(filters.command("nightmode") & filters.group)
@block_dec
async def nightmode_on_handler(_, message: Message):
    chat_id = message.chat.id
    
    # Check if user is admin
    try:
        member = await app.get_chat_member(chat_id, message.from_user.id)
        if not member.privileges or not member.privileges.can_change_info:
            return await message.reply("❌ Only admins can use this command")
    except Exception:
        return await message.reply("❌ Failed to check admin status")

    arg = message.command[1] if len(message.command) > 1 else None

    if arg == "on":
        await nightmode_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"chat_id": chat_id}},
            upsert=True
        )
        await message.reply(
            "✅ **Night Mode Enabled!**\n\n"
            "Group will be locked at 12:00 AM (IST) and unlocked at 6:00 AM (IST).",
            reply_markup=button_row
        )

    elif arg == "off":
        await nightmode_collection.delete_one({"chat_id": chat_id})
        await unlock_chat(chat_id)
        await message.reply("❌ **Night Mode Disabled!**\n\nGroup unlocked and night mode removed.")

    else:
        await message.reply("Usage: `/nightmode on` or `/nightmode off`")

async def job_close():
    async for chat in nightmode_collection.find({}):
        try:
            await app.send_message(
                chat["chat_id"],
                "🌙 **12:00 AM** → Group is closing till 6:00 AM.\n"
                "Night Mode started! Good night everyone! 😴",
                reply_markup=button_row
            )
            await lock_chat(chat["chat_id"])
        except RPCError as e:
            print(f"Error in job_close for chat {chat['chat_id']}: {e}")
        except Exception as e:
            print(f"Unexpected error in job_close: {e}")

async def job_open():
    async for chat in nightmode_collection.find({}):
        try:
            await app.send_message(
                chat["chat_id"],
                "☀️ **06:00 AM** → Group is opening.\n"
                "Night Mode ended! Good morning everyone! 🌅"
            )
            await unlock_chat(chat["chat_id"])
        except RPCError as e:
            print(f"Error in job_open for chat {chat['chat_id']}: {e}")
        except Exception as e:
            print(f"Unexpected error in job_open: {e}")

# Initialize scheduler
scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")

# Initialize function to start scheduler
def initialize_nightmode():
    scheduler.add_job(job_close, trigger="cron", hour=0, minute=0)
    scheduler.add_job(job_open, trigger="cron", hour=6, minute=0)
    if not scheduler.running:
        scheduler.start()
        print("✅ Night Mode scheduler started")
    return scheduler
