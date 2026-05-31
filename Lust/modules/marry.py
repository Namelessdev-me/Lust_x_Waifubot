import asyncio
import random
import time
from pyrogram import Client, filters
from . import user_collection, collection, capsify, app, db
from .block import block_dec, temp_block
from datetime import datetime

cooldown_collection = db.cooldowns
AUTO_DELETE_SECONDS = 120  # 2 minutes

async def auto_delete(msg, delay=AUTO_DELETE_SECONDS):
    """Delete a message after `delay` seconds."""
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass

async def get_cooldown_from_db(user_id):
    try:
        user_data = await cooldown_collection.find_one({'id': user_id})
        if user_data and 'last_roll' in user_data:
            return user_data['last_roll']
        return None
    except Exception as e:
        print(f"Error retrieving cooldown from DB: {e}")
        return None

async def update_cooldown_in_db(user_id):
    try:
        current_time = datetime.utcnow()
        await cooldown_collection.update_one(
            {'id': user_id},
            {'$set': {'last_roll': current_time}},
            upsert=True
        )
    except Exception as e:
        print(f"Error updating cooldown in DB: {e}")

async def get_unique_characters(receiver_id, target_rarities =['⚪ Common', '☘️ Medium', '🔴 Rare', '🟡 Legendary', '🔮 Limited']):
    try:
        user = await user_collection.find_one({'id': receiver_id}, {'characters': 1})
        owned_ids = [char['id'] for char in user['characters']] if user and 'characters' in user else []
        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}, 'id': {'$nin': owned_ids}}},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        if not characters:
            fallback_pipeline = [
                {'$match': {'rarity': {'$in': target_rarities}}},
                {'$sample': {'size': 1}}
            ]
            cursor = collection.aggregate(fallback_pipeline)
            characters = await cursor.to_list(length=None)
        return characters
    except Exception:
        return []

async def send_error_report(client, message, error_message):
    report_message = (
        f"{capsify('Error')}: {error_message}\n"
        f"{capsify('Please report this issue')}: @LustXGroups"
    )
    sent = await client.send_message(
        chat_id=message.chat.id,
        text=report_message,
        reply_to_message_id=message.id
    )
    asyncio.create_task(auto_delete(sent))

async def handle_marriage(client, message, receiver_id):
    try:
        unique_characters = await get_unique_characters(receiver_id)
        if not unique_characters:
            await send_error_report(client, message, "Failed to retrieve characters. Please try again later.")
            return

        await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': {'$each': unique_characters}}})

        for character in unique_characters:
            caption = (
                f"{capsify('Congratulations')}! {message.from_user.first_name}, {capsify('you are now married ')}! "
                f"{capsify('Here is your character')}:\n"
                f"Waifu: {character['name']}\n"
                f"Rarity: {character['rarity']}\n"
                f"Anime: {character['anime']}\n"
            )
            sent = await client.send_photo(
                chat_id=message.chat.id,
                photo=character['img_url'],
                caption=caption,
                reply_to_message_id=message.id
            )
            asyncio.create_task(auto_delete(sent))

    except Exception as e:
        await send_error_report(client, message, str(e))

async def handle_dice(client, message, receiver_id):
    try:
        dice_message = await client.send_dice(chat_id=message.chat.id)
        value = int(dice_message.dice.value)
        asyncio.create_task(auto_delete(dice_message))

        if value in [1, 6]:
            unique_characters = await get_unique_characters(receiver_id)
            if not unique_characters:
                await send_error_report(client, message, "Failed to retrieve characters. Please try again later.")
                return

            for character in unique_characters:
                await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': character}})

            for character in unique_characters:
                caption = (
                    f"{capsify('Congratulations')}! {message.from_user.first_name}, {capsify('Wow she accepted now you are married! 🪼')}! "
                    f"{capsify('Here is your character')}:\n"
                    f"Name: {character['name']}\n"
                    f"Rarity: {character['rarity']}\n"
                    f"Anime: {character['anime']}\n"
                )
                sent = await client.send_photo(
                    chat_id=message.chat.id,
                    photo=character['img_url'],
                    caption=caption,
                    reply_to_message_id=message.id
                )
                asyncio.create_task(auto_delete(sent))
        else:
            sent = await client.send_message(
                chat_id=message.chat.id,
                text=f"{message.from_user.first_name}, {capsify('your marriage proposal was rejected she walk away s')}! 🤧",
                reply_to_message_id=message.id
            )
            asyncio.create_task(auto_delete(sent))

    except Exception as e:
        await send_error_report(client, message, str(e))

@app.on_message(filters.command("marry"))
@block_dec
async def dice_command(client, message):
    user_id = message.from_user.id

    if temp_block(user_id):
        return

    last_roll_time = await get_cooldown_from_db(user_id)

    if last_roll_time:
        cooldown_time = (datetime.utcnow() - last_roll_time).total_seconds()

        if cooldown_time < 45:
            remaining_time = int(45 - cooldown_time)

            sent = await client.send_message(
                chat_id=message.chat.id,
                text=capsify(f"Please wait {remaining_time} seconds before rolling again."),
                reply_to_message_id=message.id
            )
            asyncio.create_task(auto_delete(sent))
            return

    await update_cooldown_in_db(user_id)

    if user_id == 7162166061:
        sent = await client.send_message(
            chat_id=message.chat.id,
            text=capsify("You are banned from using this command."),
            reply_to_message_id=message.id
        )
        asyncio.create_task(auto_delete(sent))
        return

    receiver_id = message.from_user.id
    await handle_dice(client, message, receiver_id)
