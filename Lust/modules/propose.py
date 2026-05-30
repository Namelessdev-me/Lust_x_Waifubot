import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import random
from datetime import datetime, timedelta
from Lust import collection, user_collection, user_totals_collection
from . import add as add_balance, deduct as deduct_balance, app, capsify
from .block import block_dec, temp_block

rarity_map = {
    "⚪ Common":    True,
    "☘️ Medium":   True,
    "🔴 Rare":     True,
    "🟡 Legendary": True,
    "💋 Nude":     False,
    "🔮 Limited":  True,
    "🐦‍🔥 Exotic": False,
    "🎐 Devine":   False,
    "💦 Wet":      False,
}

last_propose_times = {}
proposing_users = {}

@app.on_message(filters.command("propose"))
@block_dec
async def propose(client, message: Message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    user_data = await user_collection.find_one({'id': user_id})

    if not user_data or int(user_data.get('balance', 0)) < 10:
        await message.reply_text(capsify("You need at least 10 Exlix to propose."))
        proposing_users[user_id] = False
        return

    if proposing_users.get(user_id):
        await message.reply_text(capsify("You are already proposing. Please wait for the current proposal to finish."))
        proposing_users[user_id] = False
        return
    else:
        proposing_users[user_id] = True

    last_propose_time = last_propose_times.get(user_id)
    if last_propose_time:
        time_since_last_propose = datetime.now() - last_propose_time
        if time_since_last_propose < timedelta(minutes=5):
            remaining_cooldown = timedelta(minutes=5) - time_since_last_propose
            remaining_cooldown_minutes = remaining_cooldown.total_seconds() // 60
            remaining_cooldown_seconds = remaining_cooldown.total_seconds() % 60
            await message.reply_text(capsify(f"Cooldown! Please wait {int(remaining_cooldown_minutes)}m {int(remaining_cooldown_seconds)}s before proposing again."))
            proposing_users[user_id] = False
            return

    await deduct_balance(user_id, 10)

    await message.reply_photo(
        photo='https://files.catbox.moe/jqpeg5.jpg',
        caption=capsify("💍 You gathered your courage and got down on one knee...")
    )

    await asyncio.sleep(2)

    await message.reply_text(capsify("💫 She's thinking... Hold your breath!"))

    await asyncio.sleep(2)

    if random.random() < 0.6:
        await message.reply_animation(
            animation='https://files.catbox.moe/kvxr63.gif',
            caption=capsify("💔 She slapped you .. Better luck next time! 😭")
        )
    else:
        all_characters = list(await collection.find({}).to_list(length=None))
        valid_characters = [char for char in all_characters if char.get('rarity') in rarity_map.keys()]

        if not valid_characters:
            await message.reply_text(capsify("No characters available with the specified rarity."))
            proposing_users[user_id] = False
            return

        character = random.choice(valid_characters)
        await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
        await message.reply_photo(
            photo=character['img_url'],
            caption=capsify(f"💖 {character['name']} blushed and said Yes! She's yours now~ 🌸")
        )

    last_propose_times[user_id] = datetime.now()
    proposing_users[user_id] = False
