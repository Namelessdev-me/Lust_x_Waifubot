from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime, timedelta
from Lust import application, user_collection
import random
from . import app, user_collection, collection, add, deduct, show, capsify

COOLDOWN_DURATION = 60
COMMAND_BAN_DURATION = 600

last_command_time = {}
user_cooldowns = {}

async def random_daily_reward(client, message):
    if message.chat.type == "private":
        await message.reply_text(capsify("This command can only be used in group chats."))
        return

    user_id = message.from_user.id

    if message.reply_to_message:
        await message.reply_text(capsify("Fuck Explore a orc den Exlix.⚡"))
        return

    if user_id in user_cooldowns and (datetime.utcnow() - user_cooldowns[user_id]) < timedelta(seconds=COOLDOWN_DURATION):
        remaining_time = COOLDOWN_DURATION - (datetime.utcnow() - user_cooldowns[user_id]).total_seconds()
        await message.reply_text(capsify(f"You must wait {int(remaining_time)} seconds before using explore again."))
        return

    user_balance = await show(user_id)
    crime_fee = 300

    if user_balance < crime_fee:
        await message.reply_text(capsify("You need at least 300 Exlix to use explore."))
        return

    await deduct(user_id, crime_fee)

    random_reward = random.randint(3000, 5000)

    congratulatory_messages = [
        "Explore a dungeon",
        "Explore a dark forest",
        "Explore ruins",
        "Explore an elvish village",
        "Explore a goblin nest",
        "Explore an orc den"
    ]
    random_message = random.choice(congratulatory_messages)

    await add(user_id, random_reward)
    last_command_time[user_id] = datetime.utcnow()
    user_cooldowns[user_id] = datetime.utcnow()

    await message.reply_text(capsify(f"You {random_message} and got {random_reward} Exlix.🤫"))

@app.on_message(filters.command("explore") & filters.group)
async def explore_command(client, message):
    await random_daily_reward(client, message)
