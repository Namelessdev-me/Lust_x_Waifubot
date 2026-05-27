from pyrogram import filters
from . import user_collection, app, capsify
from .block import block_dec, temp_block
from Lust.utils import show, add, deduct, smex, sbank
from Lust.config import OWNER_ID

@app.on_message(filters.command("addexlic") & filters.user(OWNER_ID))
async def add_exlic_cmd(client, message):
    args = message.text.split()[1:]

    try:
        if message.reply_to_message:
            target_id  = message.reply_to_message.from_user.id
            target_name = message.reply_to_message.from_user.first_name
            amount = int(args[0])
        else:
            target_id  = int(args[0])
            amount     = int(args[1])
            user_data  = await user_collection.find_one({"id": target_id})
            target_name = user_data.get("first_name", str(target_id)) if user_data else str(target_id)
    except (IndexError, ValueError):
        await message.reply_text(
            capsify("Usage:\n/addexlic <user_id> <amount>\nOR reply to user: /addexlic <amount>")
        )
        return

    if amount <= 0:
        await message.reply_text(capsify("❌ Amount must be positive!"))
        return

    await add(target_id, amount)
    new_bal = await show(target_id)

    await message.reply_text(
        capsify(
            f"✅ Exlic Added!\n\n"
            f"👤 User   : {target_name}\n"
            f"🆔 ID     : {target_id}\n"
            f"➕ Added  : {amount:,} Exlic\n"
            f"💰 New Bal: {new_bal:,} Exlic"
        )

@app.on_message(filters.command("subexlic") & filters.user(OWNER_ID))
async def sub_exlic_cmd(client, message):
    args = message.text.split()[1:]

    try:
        if message.reply_to_message:
            target_id   = message.reply_to_message.from_user.id
            target_name = message.reply_to_message.from_user.first_name
            amount = int(args[0])
        else:
            target_id  = int(args[0])
            amount     = int(args[1])
            user_data  = await user_collection.find_one({"id": target_id})
            target_name = user_data.get("first_name", str(target_id)) if user_data else str(target_id)
    except (IndexError, ValueError):
        await message.reply_text(
            capsify("Usage:\n/subexlic <user_id> <amount>\nOR reply to user: /subexlic <amount>")
        )
        return

    if amount <= 0:
        await message.reply_text(capsify("❌ Amount must be positive!"))
        return

    current = await show(target_id)
    if amount > current:
        await message.reply_text(
            capsify(f"❌ User only has {current:,} Exlic. Cannot deduct {amount:,}!")
        )
        return

    await deduct(target_id, amount)
    new_bal = await show(target_id)

    await message.reply_text(
        capsify(
            f"✅ Exlic Deducted!\n\n"
            f"👤 User    : {target_name}\n"
            f"🆔 ID      : {target_id}\n"
            f"➖ Deducted: {amount:,} Exlic\n"
            f"💰 New Bal : {new_bal:,} Exlic"
        )
    )


@app.on_message(filters.command("suballexlic") & filters.user(OWNER_ID))
async def sub_all_exlic_cmd(client, message):
    args = message.text.split()[1:]

    try:
        amount = int(args[0])
    except (IndexError, ValueError):
        await message.reply_text(capsify("Usage: /suballexlic <amount>"))
        return

    if amount <= 0:
        await message.reply_text(capsify("❌ Amount must be positive!"))
        return

    processing_msg = await message.reply_text(capsify("⏳ Processing all users..."))

    count      = 0
    skipped    = 0
    all_users  = await user_collection.find({}).to_list(length=None)

    for user in all_users:
        uid     = user.get("id")
        balance = int(user.get("balance", 0))
        if balance >= amount:
            await deduct(uid, amount)
            count += 1
        else:

            if balance > 0:
                await deduct(uid, balance)
                count += 1
            skipped += 1

    await processing_msg.edit_text(
        capsify(
            f"✅ Done!\n\n"
            f"➖ Deducted  : {amount:,} Exlic\n"
            f"👥 Affected  : {count} users\n"
            f"⚠️ Skipped   : {skipped} users (had less than amount, zeroed out)"
        )
    )
