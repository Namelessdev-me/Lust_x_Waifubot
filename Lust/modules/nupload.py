from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import ReturnDocument
import random
import re
from . import uploader_filter, app
from Lust import collection, db, CHARA_CHANNEL_ID
from .upload import CATEGORY_MAP


rarity_map = {
    1: "⚪ Common",
    2: "☘️ Medium",
    3: "🔴 Rare",
    4: "🟡 Legendary",
    5: "💋 Nude",
    6: "🔮 Limited",
    7: "🐦‍🔥 Exotic",
    8: "🎐 Devine",
    9: "💦 Wet",
    10: "🎥 Animation"
}


async def get_next_character_id():
    characters = await collection.find({}, {"id": 1, "_id": 0}).to_list(length=None)

    used_ids = sorted(int(c["id"]) for c in characters if "id" in c)

    current = 1
    for uid in used_ids:
        if uid == current:
            current += 1
        else:
            break

    return current




@app.on_message(filters.command('upload') & uploader_filter)
async def upload(client: Client, message: Message):
    replied = message.reply_to_message
    if not replied or (not replied.photo and not replied.video):
        await message.reply_text(
            "📝 Upload Format:\n"
            "Reply to an image or video with caption:\n\n"
            "Name - Character Name\n"
            "Anime - Anime Name\n"
            "Rarity - 1 to 9\n"
            "Price - 83"
        )
        return

    caption = message.reply_to_message.caption
    if not caption:
        await message.reply_text("Please add caption to the image!")
        return

    caption = caption.encode("utf-8", "ignore").decode()

    caption_lines = caption.strip().split("\n")

    try:
        character_name = None
        anime = None
        rarity_str = None
        price = None

        for line in caption_lines:
            if "Name - " in line:
                character_name = line.split("Name - ")[1].strip().title()

            elif "Anime - " in line:
                anime = line.split("Anime - ")[1].strip().title()

            elif "Rarity - " in line:
                rarity_str = line.split("Rarity - ")[1].strip()

            elif "Price - " in line:
                price_str = line.split("Price - ")[1].strip()
                price_str = price_str.replace(",", "").replace(" ", "")
                price = int(price_str)

        missing = []

        if not character_name:
            missing.append("Name")
        if not anime:
            missing.append("Anime")
        if not rarity_str:
            missing.append("Rarity")
        if price is None:
            missing.append("Price")

        if missing:
            await message.reply_text(
                "❌ Missing required fields:\n• " + "\n• ".join(missing)
            )
            return

        rarity_num = int(rarity_str)

        is_video = bool(message.reply_to_message.video)
        if is_video:
            rarity = "🎥 Animation"
        else:
            if rarity_num not in rarity_map or rarity_num == 10:
                await message.reply_text("❌ Invalid rarity! Use 1–9")
                return
            rarity = rarity_map[rarity_num]

    except Exception as e:
        await message.reply_text(f"❌ Error parsing caption: {e}")
        return

    try:
        replied = message.reply_to_message
        is_video = bool(replied.video)


        if is_video:
            file_id = replied.video.file_id
        else:
            file_id = replied.photo.file_id

        id = str(await get_next_character_id()).zfill(2)


        rarity_emoji = rarity.split(" ")[0]
        rarity_name = rarity.split(" ", 1)[1]
        emoji_match = re.search(r'\[(.*?)\]', character_name)
        category_line = ""
        if emoji_match:
            emoji = emoji_match.group(1)
            if emoji in CATEGORY_MAP:
                category_line = CATEGORY_MAP[emoji]

        added_by = message.from_user.first_name

        chan_caption = (
            f"OwO! Check out this character!\n\n"
            f"{anime}\n"
            f"{id}: {character_name}\n\n"
            f"({rarity_emoji} 𝙍𝘼𝙍𝙄𝙏𝙔: {rarity_name})\n"
        )
        if category_line:
            chan_caption += f"\n{category_line}\n"
        chan_caption += f"\n➼ ᴀᴅᴅᴇᴅ ʙʏ: {added_by}"

        from Lust import CHARA_CHANNEL_ID
        if is_video:
            sent_message = await client.send_video(
                chat_id=CHARA_CHANNEL_ID,
                video=file_id,
                caption=chan_caption
            )
        else:
            sent_message = await client.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=file_id,
                caption=chan_caption
            )

        character = {
            "img_url": file_id,
            "type": "video" if is_video else "photo",
            "name": character_name,
            "anime": anime,
            "rarity": rarity,
            "price": price,
            "id": id,
            "message_id": sent_message.id
        }

        await collection.insert_one(character)

        await message.reply_text(
            f"✅ CHARACTER ADDED SUCCESSFULLY!\n\n"
            f"{'🎥' if is_video else '🖼'} Type  : {'Video' if is_video else 'Photo'}\n"
            f"👤 Name  : {character_name}\n"
            f"📺 Anime : {anime}\n"
            f"✨ Rarity: {rarity}\n"
            f"💰 Price : {formatted_price} Exlic\n"
            f"🆔 ID    : {id}"
        )

    except Exception as e:
        await message.reply_text(f"❌ An error occurred: {e}")

