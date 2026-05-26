from pyrogram import filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
import random
from datetime import datetime

from . import user_collection, app, capsify
from Lust import *
from .block import block_dec, temp_block, block_cbq

sudb = db.sudo
devb = db.dev
uploaderdb = db.uploader

BOT_NAME = "Aɴɪ Fᴇᴛᴄʜᴇʀ Bᴏᴛ"

START_STICKER = "CAACAgUAAyEFAATU_5CsAAIBqWlJghT2EjowZC7owffFiuxtp-4TAAIxGQACii1pVUCIjbDJmGJTHgQ"

start_text = f"""
┬── ⋅ ⋅ ───── ᯽ ───── ⋅ ⋅ ──┬
  Kση'ηɪᴄʜɪᴡᴧ !
┴── ⋅ ⋅ ───── ᯽ ───── ⋅ ⋅ ──┴

────────────────────────
│ ᴡєʟᴄσϻє ᴛσ Lust Slave bot, ʏσυꝛ ғʀɪєηᴅʟʏ ꜱʟᴀᴠᴇ ʙσᴛ ☄ │
────────────────────────

━━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ 
 ❖ ɪ ᴡɪʟʟ ᴀυᴛᴏ-ꜱᴘᴀᴡɴ ɴᴇᴡ ꜱʟᴀᴠᴇꜱ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴀғᴛᴇʀ 100 ᴍᴇꜱꜱᴀɢᴇꜱ.
 ❖ ʏᴏᴜ ᴄᴀɴ ᴄυꜱᴛᴏᴍɪᴢᴇ ᴍʏ ꜱᴇᴛᴛɪɴɢꜱ ᴛᴏ ꜱυɪᴛ ʏᴏᴜʀ ᴘʟᴀʏꜱᴛʏʟᴇ.
━━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ 

──────────────────────
❖ ʜᴏᴡ ᴛᴏ ᴜꜱᴇ ᴍᴇ:
 ➟ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ & sᴛᴀʀᴛ ғᴇᴛᴄʜɪɴɢ.
──────────────────────
"""

credits_text = (
    "Bot Credits\n\n"
    "Users below are the developers, uploaders, etc.\n"
    "Please contact only for valid issues.\n\n"
    "Thank You!"
)

support_buttons = [
    [
        IKB(capsify("Support"), url=f"https://t.me/{SUPPORT_CHAT}"),
        IKB(capsify("Updates"), url=f"https://t.me/{UPDATE_CHAT}")
    ],
    [
        IKB(capsify("Add Me 🐥"), url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
    ],
    [
        IKB(capsify("Help"), url=f"https://t.me/{SUPPORT_CHAT}"),
        IKB(capsify("Credits"), callback_data="credits")
    ]
]

# ─────────────── START PRIVATE ───────────────

@app.on_message(filters.command("start") & filters.private)
@block_dec
async def startp(_, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    user = await _.get_users(user_id)

    data = await user_collection.find_one({"id": user_id})

    if data:
        user_collection.update_one(
            {"id": user_id},
            {"$set": {
                "username": user.username,
                "first_name": user.first_name
            }}
        )
    else:
        user_collection.insert_one({
            "id": user_id,
            "username": user.username,
            "first_name": user.first_name,
            "balance": 0,
            "saved_amount": 0,
            "characters": [],
            "loan_amount": 0,
            "created_at": datetime.now()
        })

    # ✅ SEND STICKER FIRST
    await _.send_sticker(
        chat_id=user_id,
        sticker=START_STICKER
    )

    # ✅ THEN SEND VIDEO + TEXT
    random_video = random.choice(PHOTO_URL)
    await _.send_video(
        chat_id=user_id,
        video=random_video,
        caption=capsify(start_text),
        reply_markup=IKM(support_buttons)
    )

# ─────────────── START GROUP ───────────────

@app.on_message(filters.command("start") & filters.group)
@block_dec
async def startg(_, message):
    if temp_block(message.from_user.id):
        return

    await message.reply_text(
        capsify("🚀 Start fetching slaves in DM!"),
        reply_markup=IKM([
            [IKB(capsify("Start in DM"), url=f"https://t.me/{BOT_USERNAME}?start=start")]
        ])
    )

# ─────────────── CREDITS HANDLERS (unchanged) ───────────────
# your existing credits / callback handlers remain SAME

@app.on_message(filters.command("credits"))
@block_dec
async def cred(_, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    await message.reply_text(
        text=capsify(credits_text),
        reply_markup=IKM([
            [IKB(capsify("Developers"), callback_data="sdev"),
             IKB(capsify("Sudos"), callback_data="ssudo")],
            [IKB(capsify("Uploads"), callback_data="suploader"),
             IKB(capsify("Back"), callback_data="main")]
        ])
    )

@app.on_callback_query(filters.regex("credits"))
@block_cbq
async def credcb(_, callback_query):
    await callback_query.edit_message_text(
        text=capsify(credits_text),
        reply_markup=IKM([
            [IKB(capsify("Developers"), callback_data="sdev"),
             IKB(capsify("Sudos"), callback_data="ssudo")],
            [IKB(capsify("Uploads"), callback_data="suploader"),
             IKB(capsify("Back"), callback_data="main")]
        ])
    )

@app.on_callback_query(filters.regex("sdev"))
@block_cbq
async def sdev(_, callback_query):
    await callback_query.edit_message_text(
        text=capsify("Loading developer names..."),
        reply_markup=IKM([
            [IKB(capsify("Back"), callback_data="credits")]
        ])
    )

    dev_buttons = []
    async for user in devb.find():
        dev_id = user.get("user_id")
        if dev_id:
            user_data = await user_collection.find_one({"id": dev_id})
            first_name = user_data.get("first_name", "Unknown") if user_data else "Unknown"
            dev_buttons.append(IKB(capsify(first_name), user_id=dev_id))

    rows = [dev_buttons[i:i+3] for i in range(0, min(len(dev_buttons), 12), 3)]
    await callback_query.edit_message_text(
        text=capsify("**Developers:**"),
        reply_markup=IKM(rows + [[IKB(capsify("Back"), callback_data="credits")]])
    )

@app.on_callback_query(filters.regex("ssudo"))
@block_cbq
async def ssudo(_, callback_query):
    await callback_query.edit_message_text(
        text=capsify("Loading sudo names..."),
        reply_markup=IKM([
            [IKB(capsify("Back"), callback_data="credits")]
        ])
    )

    sudo_buttons = []
    async for user in sudb.find():
        sudo_id = user.get("user_id")
        if sudo_id:
            user_data = await user_collection.find_one({"id": sudo_id})
            first_name = user_data.get("first_name", "Unknown") if user_data else "Unknown"
            sudo_buttons.append(IKB(capsify(first_name), user_id=sudo_id))

    rows = [sudo_buttons[i:i+3] for i in range(0, min(len(sudo_buttons), 12), 3)]
    await callback_query.edit_message_text(
        text=capsify("**Sudos:**"),
        reply_markup=IKM(rows + [[IKB(capsify("Back"), callback_data="credits")]])
    )

@app.on_callback_query(filters.regex("suploader"))
@block_cbq
async def suploader(_, callback_query):
    await callback_query.edit_message_text(
        text=capsify("Loading uploader names..."),
        reply_markup=IKM([
            [IKB(capsify("Back"), callback_data="credits")]
        ])
    )

    uploader_buttons = []
    async for user in uploaderdb.find():
        uploader_id = user.get("user_id")
        if uploader_id:
            user_data = await user_collection.find_one({"id": uploader_id})
            first_name = user_data.get("first_name", "Unknown") if user_data else "Unknown"
            uploader_buttons.append(IKB(capsify(first_name), user_id=uploader_id))

    rows = [uploader_buttons[i:i+3] for i in range(0, min(len(uploader_buttons), 12), 3)]
    await callback_query.edit_message_text(
        text=capsify("**Uploaders:**"),
        reply_markup=IKM(rows + [[IKB(capsify("Back"), callback_data="credits")]])
    )

@app.on_callback_query(filters.regex("main"))
async def main(_, callback_query):
    random_video = random.choice(PHOTO_URL)
    await callback_query.edit_message_text(
        text=capsify(start_text),
        reply_markup=IKM(support_buttons)
    )
