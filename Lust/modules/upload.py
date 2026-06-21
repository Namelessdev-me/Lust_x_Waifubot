from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import UpdateOne
import re
import asyncio
import random

from . import sudo_filter, app, capsify
from Lust import collection, CHARA_CHANNEL_ID, user_collection
from . import uploader_filter


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
10: "🎥 Animation",
11: "☔ Rainy",
12: "🔖 Manga",
13: "🍭 Cosplay",
14: "☀️ Sunny",
15: "❄️ Winter",
16: "🪼 Cosmic"
}


# Auto-price ranges per rarity number (min, max) — used to randomly
# assign a price on /upload instead of requiring manual entry.
PRICE_RANGES = {
1: (1_000, 4_000),
2: (5_000, 16_000),
3: (20_000, 60_000),
4: (80_000, 200_000),
5: (16_000_000, 50_000_000),
6: (600_000, 1_600_000),
7: (50_000_000, 200_000_000),
8: (2_000_000, 5_000_000),
9: (4_000_000, 10_000_000),
10: (8_000_000, 20_000_000),
11: (200_000, 600_000),
12: (250_000, 700_000),
13: (5_000_000, 15_000_000),
14: (200_000, 600_000),
15: (200_000, 600_000),
16: (25_000_000, 80_000_000)
}


PRICE_RANGE_TEXT = (
"✨ ᴘʀɪᴄᴇ ʀᴀɴɢᴇ ʟɪꜱᴛ\n"
"━━━━━━━━━━━━━━━━━━━━\n\n"
"1. ⚪ ᴄᴏᴍᴍᴏɴ\n"
"💰 1k - 4k ᴄᴏɪɴs\n\n"
"2. ☘️ ᴍᴇᴅɪᴜᴍ\n"
"💰 5k - 16k ᴄᴏɪɴs\n\n"
"3. 🔴 ʀᴀʀᴇ\n"
"💰 20k - 60k ᴄᴏɪɴs\n\n"
"4. 🟡 ʟᴇɢᴇɴᴅᴀʀʏ\n"
"💰 80k - 200k ᴄᴏɪɴs\n\n"
"5. 💋 ɴᴜᴅᴇ\n"
"💰 16m - 50m ᴄᴏɪɴs\n\n"
"6. 🔮 ʟɪᴍɪᴛᴇᴅ\n"
"💰 600k - 1.6m ᴄᴏɪɴs\n\n"
"7. 🐦‍🔥 ᴇxᴏᴛɪᴄ\n"
"💰 50m - 200m+ ᴄᴏɪɴs\n\n"
"8. 🎐 ᴅᴇᴠɪɴᴇ\n"
"💰 2m - 5m ᴄᴏɪɴs\n\n"
"9. 💦 ᴡᴇᴛ\n"
"💰 4m - 10m ᴄᴏɪɴs\n\n"
"10. 🎥 ᴀɴɪᴍᴀᴛɪᴏɴ\n"
"💰 8m - 20m ᴄᴏɪɴs\n\n"
"11. ☔ ʀᴀɪɴʏ\n"
"💰 200k - 600k ᴄᴏɪɴs\n\n"
"12. 🔖 ᴍᴀɴɢᴀ\n"
"💰 250k - 700k ᴄᴏɪɴs\n\n"
"13. 🍭 ᴄᴏꜱᴘʟᴀʏ\n"
"💰 5m - 15m ᴄᴏɪɴs\n\n"
"14. ☀️ ꜱᴜɴɴʏ\n"
"💰 200k - 600k ᴄᴏɪɴs\n\n"
"15. ❄️ ᴡɪɴᴛᴇʀ\n"
"💰 200k - 600k ᴄᴏɪɴs\n\n"
"16. 🪼 ᴄᴏꜱᴍɪᴄ\n"
"💰 25m - 80m ᴄᴏɪɴs\n\n"
"━━━━━━━━━━━━━━━━━━━━\n"
"💡 ᴠᴀʟᴜᴇ ᴅᴇᴘᴇɴᴅꜱ ᴏɴ\n"
"• ᴘᴏᴘᴜʟᴀʀɪᴛʏ\n"
"• ᴇᴅɪᴛꜱ / ᴀʀᴛ\n"
"• ᴅᴇᴍᴀɴᴅ\n"
"• ᴛʀᴀᴅᴇ ᴠᴀʟᴜᴇ"
)


CATEGORY_MAP = {
'🎒': '🎒 𝑪𝒍𝒂𝒔𝒔𝒓𝒐𝒐𝒎 𝑸𝒖𝒆𝒆𝒏 🎒',
'💉': '💉 𝑾𝒉𝒊𝒕𝒆 𝑮𝒓𝒂𝒄𝒆 💉',
'🧹': '🧹 𝑪𝒉𝒂𝒓𝒎 𝑴𝒂𝒊𝒅𝒆𝒏 🧹',
'🐰': '🐰 𝑴𝒐𝒐𝒏𝒍𝒊𝒕 𝑩𝒐𝒖𝒏𝒄𝒆 🐰',
'👘': '👘 𝑺𝒂𝒌𝒖𝒓𝒂 𝑮𝒓𝒂𝒄𝒆 👘',
'💍': '💍 𝑭𝒐𝒓𝒆𝒗𝒆𝒓 𝑩𝒍𝒊𝒔𝒔 💍',
'🎊': '🎊 𝑽𝒊𝒃𝒆 𝑬𝒏𝒆𝒓𝒈𝒚 🎊',
'🚓': '🚓 𝑱𝒖𝒔𝒕𝒊𝒄𝒆 𝑬𝒏𝒄𝒉𝒂𝒏𝒕𝒓𝒆𝒔𝒔 🚓',
'🥻': '🥻 𝑬𝒕𝒉𝒆𝒓𝒆𝒂𝒍 𝑮𝒆𝒎 🥻',
'🕷': '🕷 𝑵𝒆𝒕 𝑺𝒐𝒓𝒄𝒆𝒓𝒆𝒔𝒔 🕷',
'🏜': '🏜 𝑺𝒂𝒏𝒅𝒔 𝑬𝒎𝒑𝒓𝒆𝒔𝒔 🏜',
'⚜️': '⚜️ 𝑺𝒂𝒄𝒓𝒆𝒅 𝑶𝒂𝒕𝒉 ⚜️',
'🩸': '🩸 𝑵𝒐𝒄𝒕𝒖𝒓𝒏𝒂𝒍 𝑹𝒐𝒔𝒆 🩸',
'🕊️': '🕊️ 𝑾𝒊𝒏𝒈𝒔 𝒐𝒇 𝑭𝒂𝒕𝒆 🕊️',
'☃️': '☃️ 𝑺𝒏𝒐𝒘𝒇𝒂𝒍𝒍 𝑬𝒍𝒍𝒆 ☃️',
'💞': '💞 𝑯𝒆𝒂𝒓𝒕𝒔𝒐𝒏𝒈 𝑫𝒖𝒄𝒉𝒆𝒔𝒔 💞',
'🏖': '🏖 𝑺𝒖𝒏𝒌𝒊𝒔𝒔 𝑺𝒆𝒓𝒆𝒏𝒂𝒅𝒆 🏖',
'🎃': '🎃 𝑺𝒑𝒆𝒍𝒍𝒃𝒐𝒖𝒏𝒅 𝑾𝒊𝒕𝒄𝒉 🎃',
'🎮': '🎮 𝑮𝒂𝒎𝒆 𝑮𝒐𝒅𝒅𝒆𝒔𝒔 🎮'
}


def build_caption(character: dict) -> str:
    """Rebuilds the channel caption from a character DB document.
    Used by /upload, /update, /r, and /resenddatabase so the channel
    post always matches whatever is currently in Mongo.
    """
    name = character.get("name", "")
    anime = character.get("anime", "")
    char_id = character.get("id", "")
    rarity = character.get("rarity", "") or ""
    char_type = character.get("char_type", "")
    added_by = character.get("added_by", "Unknown")

    if " " in rarity:
        rarity_emoji, rarity_name = rarity.split(" ", 1)
    else:
        rarity_emoji, rarity_name = rarity, rarity

    emoji_match = re.search(r'\[(.*?)\]', name)
    category_line = ""
    if emoji_match:
        emoji = emoji_match.group(1)
        if emoji in CATEGORY_MAP:
            category_line = CATEGORY_MAP[emoji]

    caption = (
        f"OwO! Check out this character!\n\n"
        f"{anime}\n"
        f"{char_id}: {name}\n\n"
        f"({rarity_emoji} 𝙍𝘼𝙍𝙄𝙏𝙔: {rarity_name})\n"
    )

    if char_type:
        caption += f"✦ ᴛʏᴘᴇ: {char_type}\n"

    if category_line:
        caption += f"\n{category_line}\n"

    caption += f"\n➼ ᴀᴅᴅᴇᴅ ʙʏ: {added_by}"

    return caption


async def get_next_character_id():
    characters = await collection.find({}, {"id": 1}).to_list(length=None)
    used_ids = sorted([int(c["id"]) for c in characters if c.get("id")])

    new_id = 1
    for cid in used_ids:
        if cid != new_id:
            break
        new_id += 1

    return str(new_id).zfill(2)


@app.on_message(filters.command("upload") & uploader_filter)
async def upload_character(client: Client, message: Message):

    reply = message.reply_to_message

    if not reply or (not reply.photo and not reply.video):
        await message.reply_text(
            "📝 Upload Format:\n"
            "Reply to a photo or video with caption:\n\n"
            "Name - Character Name\n"
            "Anime - Anime Name\n"
            "Rarity - 1 to 16\n"
            "Type - Waifu/Husbando etc.\n\n"
            "💡 Price is now set automatically based on rarity.\n\n"
            + PRICE_RANGE_TEXT
        )
        return

    if not reply.caption:
        await message.reply_text(
            "❌ Please add caption to the photo/video!\n\n"
            "Format:\nName - ...\nAnime - ...\nRarity - 1 to 16\nType - ..."
        )
        return

    caption = reply.caption

    name = re.search(r"Name\s*-\s*(.*)", caption)
    anime = re.search(r"Anime\s*-\s*(.*)", caption)
    rarity_match = re.search(r"Rarity\s*-\s*(\d+)", caption)
    type_match = re.search(r"Type\s*-\s*(.*)", caption)

    missing = []
    if not name:       missing.append("Name")
    if not anime:      missing.append("Anime")
    if not rarity_match: missing.append("Rarity")
    if not type_match:  missing.append("Type")

    if missing:
        await message.reply_text(
            f"❌ Missing fields: {', '.join(missing)}\n\n"
            f"Format:\nName - ...\nAnime - ...\nRarity - 1 to 16\nType - ..."
        )
        return

    name = name.group(1).strip()
    anime = anime.group(1).strip()
    rarity_number = int(rarity_match.group(1))
    char_type = type_match.group(1).strip()


    if reply.video:
        rarity_number = 10
        rarity = rarity_map[10]
    else:
        if rarity_number == 10:
            await message.reply_text("❌ Rarity 10 (Animation) is reserved for video uploads only.")
            return
        rarity = rarity_map.get(rarity_number)
        if not rarity:
            await message.reply_text(
                "❌ Invalid rarity! Use a number from the list below:\n\n" + PRICE_RANGE_TEXT
            )
            return

    price = random.randint(*PRICE_RANGES[rarity_number])

    char_id = await get_next_character_id()
    added_by = message.from_user.first_name

    final_caption = build_caption({
        "id": char_id,
        "name": name,
        "anime": anime,
        "rarity": rarity,
        "char_type": char_type,
        "added_by": added_by
    })

    if reply.photo:

        file_id = reply.photo.file_id

        sent = await client.send_photo(
            CHARA_CHANNEL_ID,
            photo=file_id,
            caption=final_caption
        )

        media_type = "photo"


    elif reply.video:

        file_id = reply.video.file_id

        sent = await client.send_video(
            CHARA_CHANNEL_ID,
            video=file_id,
            caption=final_caption
        )

        media_type = "video"

    else:
        await message.reply_text("Reply to photo or video.")
        return


    await collection.insert_one({
        "id": char_id,
        "name": name,
        "anime": anime,
        "rarity": rarity,
        "char_type": char_type,
        "price": price,
        "img_url": file_id,
        "type": media_type,
        "message_id": sent.id,
        "added_by": added_by
    })


    await message.reply_text(f"Character added with ID {char_id} 💰 Price: {price:,}")



@app.on_message(filters.command("delete") & sudo_filter)
async def delete_character(client: Client, message: Message):
    args = message.text.split(maxsplit=1)[1:]
    if len(args) != 1:
        await message.reply_text(capsify("Use: /delete id"))
        return

    character_id = args[0].strip()
    character = await collection.find_one_and_delete({"id": character_id})

    if not character:
        await message.reply_text(capsify(f"❌ Character with ID {character_id} not found!"))
        return


    try:
        await client.delete_messages(CHARA_CHANNEL_ID, character["message_id"])
    except Exception:
        pass

    
    bulk = []
    async for user in user_collection.find():
        if "characters" in user:
            original_len = len(user["characters"])
            user["characters"] = [c for c in user["characters"] if c["id"] != character_id]
            if len(user["characters"]) != original_len:
                bulk.append(UpdateOne({"_id": user["_id"]}, {"$set": {"characters": user["characters"]}}))

    if bulk:
        await user_collection.bulk_write(bulk)

    char_name = character.get("name", "Unknown")
    char_anime = character.get("anime", "Unknown")
    char_rarity = character.get("rarity", "Unknown")

    await message.reply_text(
        capsify(
            f"✅ Character Deleted Successfully!\n\n"
            f"🆔 ID: {character_id}\n"
            f"👤 Name: {char_name}\n"
            f"📺 Anime: {char_anime}\n"
            f"✨ Rarity: {char_rarity}\n\n"
            f"🗑 Removed from {len(bulk)} user(s) collection."
        )
    )

@app.on_message(filters.command("update") & uploader_filter)
async def update_character(client: Client, message: Message):
    args=message.text.split(maxsplit=3)[1:]
    if len(args)!=3:
        await message.reply_text("Use: /update id field value")
        return
    char_id,field,value=args
    character=await collection.find_one({"id":char_id})
    if not character:
        await message.reply_text("Character not found")
        return
    valid=["name","anime","rarity","price","img_url","char_type"]
    if field not in valid:
        await message.reply_text("Invalid field")
        return
    if field in ["name","anime"]:
        value=value.replace("-"," ").title()
    if field=="rarity":
        try:
            value=rarity_map[int(value)]
        except:
            await message.reply_text("Invalid rarity")
            return
    if field=="price":
        try:
            value=int(value)
        except:
            await message.reply_text("Invalid price")
            return
    await collection.update_one({"id":char_id},{"$set":{field:value}})
    bulk=[]
    async for user in user_collection.find():
        if "characters" in user:
            for c in user["characters"]:
                if c["id"]==char_id:
                    c[field]=value
            bulk.append(UpdateOne({"_id":user["_id"]},{"$set":{"characters":user["characters"]}}))
    if bulk:
        await user_collection.bulk_write(bulk)

    character[field] = value
    if field != "img_url" and character.get("message_id"):
        try:
            await client.edit_message_caption(
                CHARA_CHANNEL_ID,
                character["message_id"],
                caption=build_caption(character)
            )
        except Exception:
            pass

    await message.reply_text("Character updated")

@app.on_message(filters.command("r") & sudo_filter)
async def update_rarity(client: Client, message: Message):
    args=message.text.split(maxsplit=2)[1:]
    if len(args)!=2:
        await message.reply_text("Use: /r id rarity")
        return
    char_id,rarity=args
    character=await collection.find_one({"id":char_id})
    if not character:
        await message.reply_text("Character not found")
        return
    try:
        rarity_value=rarity_map[int(rarity)]
    except:
        await message.reply_text("Invalid rarity")
        return
    await collection.update_one({"id":char_id},{"$set":{"rarity":rarity_value}})
    bulk=[]
    async for user in user_collection.find():
        if "characters" in user:
            for c in user["characters"]:
                if c["id"]==char_id:
                    c["rarity"]=rarity_value
            bulk.append(UpdateOne({"_id":user["_id"]},{"$set":{"characters":user["characters"]}}))
    if bulk:
        await user_collection.bulk_write(bulk)

    character["rarity"] = rarity_value
    if character.get("message_id"):
        try:
            await client.edit_message_caption(
                CHARA_CHANNEL_ID,
                character["message_id"],
                caption=build_caption(character)
            )
        except Exception:
            pass

    await message.reply_text("Rarity updated")

@app.on_message(filters.command("resenddatabase") & sudo_filter)
async def resend_database(client: Client, message: Message):
    characters = await collection.find().sort("id", 1).to_list(length=None)

    if not characters:
        await message.reply_text("No characters found")
        return

    status = await message.reply_text(
        f"⏳ Resending {len(characters)} character(s) to the database channel...\n"
        f"This may take a while, please don't spam commands."
    )

    sent_count = 0
    failed_ids = []

    for character in characters:
        try:
            old_msg_id = character.get("message_id")
            if old_msg_id:
                try:
                    await client.delete_messages(CHARA_CHANNEL_ID, old_msg_id)
                except Exception:
                    pass

            caption = build_caption(character)
            media_type = character.get("type", "photo")
            file_id = character.get("img_url")

            if media_type == "video":
                sent = await client.send_video(
                    CHARA_CHANNEL_ID,
                    video=file_id,
                    caption=caption
                )
            else:
                sent = await client.send_photo(
                    CHARA_CHANNEL_ID,
                    photo=file_id,
                    caption=caption
                )

            await collection.update_one(
                {"_id": character["_id"]},
                {"$set": {"message_id": sent.id}}
            )
            sent_count += 1

        except Exception:
            failed_ids.append(character.get("id", "?"))

        await asyncio.sleep(0.7)  # avoid Telegram flood-wait on large databases

    result_text = f"✅ Resent {sent_count}/{len(characters)} character(s) to the database channel."
    if failed_ids:
        result_text += f"\n❌ Failed IDs: {', '.join(failed_ids)}"

    await status.edit_text(result_text)
