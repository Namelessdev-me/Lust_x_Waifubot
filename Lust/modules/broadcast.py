from pyrogram import filters
from pyrogram.types import Message
from datetime import datetime
import asyncio

from . import user_collection, app, capsify
from Lust import *
from .block import block_dec, temp_block


# ─────────────── HELPERS ───────────────

async def is_sudo_or_dev(user_id: int) -> bool:
    sudo = await db.sudo.find_one({"user_id": user_id})
    dev = await db.dev.find_one({"user_id": user_id})
    return bool(sudo or dev)


# ─────────────── BROADCAST ───────────────

@app.on_message(filters.command("broadcast") & filters.private)
@block_dec
async def broadcast(client, message: Message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    if not await is_sudo_or_dev(user_id):
        await message.reply_text(capsify("You don't have permission to use this command."))
        return

    if not message.reply_to_message:
        await message.reply_text(capsify("Reply to a message to broadcast it."))
        return

    status_msg = await message.reply_text(capsify("📡 Broadcasting... Please wait."))

    target = message.reply_to_message
    sent = 0
    failed = 0
    blocked = 0

    async for user in user_collection.find({}, projection={"id": 1}):
        uid = user.get("id")
        if not uid:
            continue
        try:
            await target.copy(uid)
            sent += 1
        except Exception as e:
            err = str(e).lower()
            if "blocked" in err or "deactivated" in err or "not found" in err:
                blocked += 1
            else:
                failed += 1
        await asyncio.sleep(0.05)  # avoid flood

    report = (
        f"Broadcast Complete\n\n"
        f"✅ Sent: {sent}\n"
        f"🚫 Blocked/Inactive: {blocked}\n"
        f"❌ Failed: {failed}\n"
        f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    await status_msg.edit_text(capsify(report))


# ─────────────── GROUP BROADCAST ───────────────

@app.on_message(filters.command("gbroadcast") & filters.private)
@block_dec
async def group_broadcast(client, message: Message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    if not await is_sudo_or_dev(user_id):
        await message.reply_text(capsify("You don't have permission to use this command."))
        return

    if not message.reply_to_message:
        await message.reply_text(capsify("Reply to a message to broadcast it to groups."))
        return

    status_msg = await message.reply_text(capsify("📡 Broadcasting to groups... Please wait."))

    target = message.reply_to_message
    sent = 0
    failed = 0

    async for group in db.groups.find({}, projection={"id": 1}):
        gid = group.get("id")
        if not gid:
            continue
        try:
            await target.copy(gid)
            sent += 1
        except Exception as e:
            failed += 1
        await asyncio.sleep(0.05)

    report = (
        f"Group Broadcast Complete\n\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}\n"
        f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    await status_msg.edit_text(capsify(report))


# ─────────────── STATS ───────────────

@app.on_message(filters.command("stats") & filters.private)
@block_dec
async def stats(client, message: Message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    if not await is_sudo_or_dev(user_id):
        await message.reply_text(capsify("You don't have permission to use this command."))
        return

    total_users = await user_collection.count_documents({})
    total_groups = await db.groups.count_documents({})

    text = (
        f"Bot Stats\n\n"
        f"👤 Total Users: {total_users}\n"
        f"👥 Total Groups: {total_groups}"
    )
    await message.reply_text(capsify(text))
    
