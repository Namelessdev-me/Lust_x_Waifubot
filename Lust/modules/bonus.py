import asyncio
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from . import app, db, capsify, user_collection, add
from .block import block_dec, temp_block, block_cbq


AUTO_DELETE_SECONDS = 120

async def auto_delete(msg, delay=AUTO_DELETE_SECONDS):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass

bonus_db = db.bonus

def get_next_day():
    tomorrow = datetime.now() + timedelta(days=1)
    return tomorrow.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d")

def get_next_week():
    today = datetime.now()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    return next_monday.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d")

async def get_bonus_status(user_id):
    record = await bonus_db.find_one({"user_id": user_id})
    if not record:
        return {"daily": None, "weekly": None}
    return record.get("bonus", {"daily": None, "weekly": None})

async def update_bonus_status(user_id, bonus_type):
    bonus_status = await get_bonus_status(user_id)
    if bonus_type == "daily":
        bonus_status["daily"] = get_next_day()
    elif bonus_type == "weekly":
        bonus_status["weekly"] = get_next_week()
    await bonus_db.update_one({"user_id": user_id}, {"$set": {"bonus": bonus_status}}, upsert=True)

@app.on_message(filters.command("bonus"))
@block_dec
async def bonus_handler(_, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    user_name = message.from_user.first_name or "User"
    today = datetime.now()
    current_day = capsify(today.strftime("%A"))
    current_week = today.strftime("%U")

    bonus_status = await get_bonus_status(user_id)
    daily_status = (
        capsify("✅ ") if bonus_status["daily"] and bonus_status["daily"] > today.strftime("%Y-%m-%d") else capsify("Available")
    )
    weekly_status = (
        capsify("✅ ") if bonus_status["weekly"] and bonus_status["weekly"] > today.strftime("%Y-%m-%d") else capsify("Available")
    )

    caption = (
        f"✦━═❖ ᴇxʟɪx ʙᴏɴᴜs ❖═━✦\n\n"
        f"• ᴜsᴇʀ : {user_name}\n"
        f"• ᴜsᴇʀ ɪᴅ : {user_id}\n"
        f"• ᴅᴀʏ : {current_day}\n"
        f"• ᴡᴇᴇᴋ : {current_week}\n\n"
        "ᴄʟᴀɪᴍ ʏᴏᴜʀ ʀᴇᴡᴀʀᴅs ʙᴇʟᴏᴡ ⬇️"
    )

    markup = IKM([
        [IKB(f"Daily: {daily_status}", callback_data=f"bonus_daily_{user_id}")],
        [IKB(f"Weekly: {weekly_status}", callback_data=f"bonus_weekly_{user_id}")],
        [IKB("Close 🗑️", callback_data=f"bo_close_{user_id}")]
    ])

    sent = await message.reply_text(caption, reply_markup=markup)
    asyncio.create_task(auto_delete(sent))

@app.on_callback_query(filters.regex(r"^bonus_"))
@block_cbq
async def bonus_claim_handler(_, query):
    _, bonus_type, user_id = query.data.split("_")
    user_id = int(user_id)

    if user_id != query.from_user.id:
        return await query.answer("This is not for you!", show_alert=True)

    today = datetime.now().strftime("%Y-%m-%d")
    bonus_status = await get_bonus_status(user_id)

    if bonus_type == "daily":
        if bonus_status["daily"] and bonus_status["daily"] > today:
            return await query.answer("You have already claimed your daily bonus!", show_alert=True)
        await add(user_id, 15000)
        await update_bonus_status(user_id, "daily")
        await query.answer("Successfully claimed your daily bonus of 15000 Exlix!", show_alert=True)

    elif bonus_type == "weekly":
        if bonus_status["weekly"] and bonus_status["weekly"] > today:
            return await query.answer("You have already claimed your weekly bonus!", show_alert=True)
        await add(user_id, 200000)
        await update_bonus_status(user_id, "weekly")
        await query.answer("Successfully claimed your weekly bonus of 200000 Exlix!", show_alert=True)

    updated_bonus_status = await get_bonus_status(user_id)
    daily_status = (
        "✅ " if updated_bonus_status["daily"] and updated_bonus_status["daily"] > today else "Available"
    )
    weekly_status = (
        "✅ " if updated_bonus_status["weekly"] and updated_bonus_status["weekly"] > today else "Available"
    )

    caption = (
        f"✦━═❖ ᴇxʟɪx ʙᴏɴᴜs ❖═━✦\n\n"
        f"• ᴜsᴇʀ : {query.from_user.first_name}\n"
        f"• ᴜsᴇʀ ɪᴅ : {user_id}\n"
        f"• ᴅᴀʏ : {datetime.now().strftime('%A')}\n"
        f"• ᴡᴇᴇᴋ : {datetime.now().strftime('%U')}\n\n"
        "ᴄʟᴀɪᴍ ʏᴏᴜʀ ʀᴇᴡᴀʀᴅs ʙᴇʟᴏᴡ ⬇️"
    )

    markup = IKM([
        [IKB(f"Daily: {daily_status}", callback_data=f"bonus_daily_{user_id}")],
        [IKB(f"Weekly: {weekly_status}", callback_data=f"bonus_weekly_{user_id}")],
        [IKB("Close 🗑️", callback_data=f"bo_close_{user_id}")]
    ])

    await query.edit_message_text(caption, reply_markup=markup)

@app.on_callback_query(filters.regex(r"^bo_close_"))
@block_cbq
async def close_bonus_handler(_, query):
    try:
        _, bonus_type, user_id = query.data.split("_")
        user_id = int(user_id)
    except ValueError:
        return

    if user_id != query.from_user.id:
        return await query.answer("This is not for you!", show_alert=True)

    await query.message.delete()
    await query.answer("Bonus menu closed!")
