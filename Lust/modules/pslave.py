from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto
from datetime import datetime, timedelta
from . import ac, rc, app, user_collection, collection, capsify 
from .block import block_dec, temp_block

async def get_claim_time(user_id):
    try:
        user_data = await user_collection.find_one({"user_id": user_id})
        if user_data and "last_claim_time" in user_data:
            return user_data["last_claim_time"]
        return None
    except Exception as e:
        print(f"Error in get_claim_time: {e}")
        return None

async def set_claim_time(user_id, claim_time):
    try:
        await user_collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_claim_time": claim_time}},
            upsert=True
        )
    except Exception as e:
        print(f"Error in set_claim_time: {e}")

async def get_chars():
    try:
        # Updated target rarities for the new 1-7 system
        target_rarities = ['⚪ Common', '☘️ Medium', '🔴 Rare', '🟡 Legendary', '🔮 Limited']
        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}}},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        chars = await cursor.to_list(length=None)
        return chars
    except Exception as e:
        print(f"Error in get_chars: {e}")
        return []

@app.on_message(filters.command("hclaim"))
@block_dec
async def pslave(client: Client, message):
    chat_id = message.chat.id
    first_name = message.from_user.first_name
    user_id = message.from_user.id

    if temp_block(user_id):
        return

    now = datetime.now()
    last_claim_date = await get_claim_time(user_id)

    if last_claim_date:
        if last_claim_date.date() == now.date():
            next_claim_time = last_claim_date + timedelta(days=1)
            remaining_time = next_claim_time - now
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            formatted_time = f"{hours:02}:{minutes:02}"
            await message.reply_text(capsify(f"Please wait for `after {formatted_time}` to claim your next slave."), quote=True)
            return

    await set_claim_time(user_id, now)

    chars = await get_chars()
    if not chars:
        await message.reply_text(capsify("No new slaves available to claim."), quote=True)
        return

    try:
        for char in chars:
            await ac(user_id, char['id'])

        img_urls = [char['img_url'] for char in chars]
        captions = [
            capsify(f"Congratulations {first_name}! You have received a new slave for your myslaves 💕!\n"
                    f"Name: {char['name']}\n"
                    f"Rarity: {char['rarity']}\n"
                    f"Anime: {char['anime']}\n")
            for char in chars
        ]
        media_group = [InputMediaPhoto(media=img_url, caption=caption) for img_url, caption in zip(img_urls, captions)]
        await message.reply_media_group(media_group)
    except Exception as e:
        print(f"Error in pslave: {e}")
        await message.reply_text(capsify("An error occurred while processing your request."), quote=True)
