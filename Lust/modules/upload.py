from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import UpdateOne
import re

from . import sudo_filter, app, capsify
from Lust import collection, CHARA_CHANNEL_ID, user_collection, db
from . import uploader_filter

# ──────────────────────────────────────────────
#  Season state  (persisted in MongoDB)
# ──────────────────────────────────────────────
season_collection = db["active_season"]

# All seasonal rarities — only ONE is active at a time
SEASONAL_RARITIES = {
    "rainy":  "☔ Rainy",
    "sunny":  "☀️ Sunny",
    "winter": "❄️ Winter",
}

async def get_active_season() -> str | None:
    """Return the currently active seasonal rarity string, or None."""
    doc = await season_collection.find_one({"_id": "season"})
    return doc["rarity"] if doc else None

async def set_active_season(rarity: str | None):
    """Set or clear the active seasonal rarity."""
    if rarity is None:
        await season_collection.delete_one({"_id": "season"})
    else:
        await season_collection.update_one(
            {"_id": "season"},
            {"$set": {"rarity": rarity}},
            upsert=True
        )

# ──────────────────────────────────────────────
#  Rarity maps
# ──────────────────────────────────────────────

# Number → rarity string (used by /upload, /r, /update)
rarity_map = {
    1:  "⚪ Common",
    2:  "☘️ Medium",
    3:  "🔴 Rare",
    4:  "🟡 Legendary",
    5:  "💋 Nude",
    6:  "🔮 Limited",
    7:  "🐦‍🔥 Exotic",
    8:  "🎐 Devine",
    9:  "💦 Wet",
    10: "🎥 Animation",
    # ── New rarities ──
    11: "☔ Rainy",
    12: "🔖 Manga",
    13: "🍭 Cosplay",
    14: "☀️ Sunny",
    15: "❄️ Winter",
    16: "🪼 Cosmic",
}

# Human-readable label for /upload help text (excludes Animation & seasonals shown separately)
STANDARD_RARITIES = {k: v for k, v in rarity_map.items() if k not in (10, 11, 14, 15)}

# Seasonal keys (name → rarity string)  — already defined above in SEASONAL_RARITIES

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
    '🎮': '🎮 𝑮𝒂𝒎𝒆 𝑮𝒐𝒅𝒅𝒆𝒔𝒔 🎮',
}


# ──────────────────────────────────────────────
#  ID helper
# ──────────────────────────────────────────────

async def get_next_character_id():
    characters = await collection.find({}, {"id": 1}).to_list(length=None)
    used_ids = sorted([int(c["id"]) for c in characters if c.get("id")])

    new_id = 1
    for cid in used_ids:
        if cid != new_id:
            break
        new_id += 1

    return str(new_id).zfill(2)


# ──────────────────────────────────────────────
#  /season  – switch the active seasonal rarity
# ──────────────────────────────────────────────

@app.on_message(filters.command("season") & sudo_filter)
async def season_cmd(client: Client, message: Message):
    args = message.text.split(maxsplit=1)

    # Show current season if no argument
    if len(args) < 2:
        current = await get_active_season()
        if current:
            await message.reply_text(
                capsify(f"🌤 Current active season: {current}\n\nUse /season <name> to switch.\nUse /season off to disable.")
            )
        else:
            await message.reply_text(
                capsify(
                    "❌ No season is currently active.\n\n"
                    "Available: rainy ☔ | sunny ☀️ | winter ❄️\n"
                    "Use /season <name> to enable one."
                )
            )
        return

    arg = args[1].strip().lower()

    # Turn off season
    if arg == "off":
        await set_active_season(None)
        await message.reply_text(capsify("✅ Season disabled. No seasonal characters will spawn."))
        return

    # Switch to a new season
    if arg not in SEASONAL_RARITIES:
        await message.reply_text(
            capsify(
                f"❌ Unknown season '{arg}'.\n\n"
                "Available: rainy ☔ | sunny ☀️ | winter ❄️\n"
                "Use /season off to disable."
            )
        )
        return

    rarity_string = SEASONAL_RARITIES[arg]
    await set_active_season(rarity_string)
    await message.reply_text(
        capsify(f"✅ Season switched to {rarity_string}!\nAll other seasonal rarities are now off.")
    )


# ──────────────────────────────────────────────
#  /upload  – add a character
# ──────────────────────────────────────────────

@app.on_message(filters.command("upload") & uploader_filter)
async def upload_character(client: Client, message: Message):

    reply = message.reply_to_message

    if not reply or (not reply.photo and not reply.video):
        await message.reply_text(
            "📝 Upload Format:\n"
            "Reply to a photo or video with caption:\n\n"
            "Name - Character Name\n"
            "Anime - Anime Name\n"
            "Rarity - (number)\n"
            "Price - 83\n\n"
            "Rarity numbers:\n"
            + "\n".join([f"{k} - {v}" for k, v in rarity_map.items() if k != 10])
            + "\n10 - 🎥 Animation (auto-set for videos)"
        )
        return

    if not reply.caption:
        await message.reply_text(
            "❌ Please add a caption to the photo/video!\n\n"
            "Format:\nName - ...\nAnime - ...\nRarity - (number)\nPrice - 83"
        )
        return

    caption = reply.caption

    name        = re.search(r"Name\s*-\s*(.*)",    caption)
    anime       = re.search(r"Anime\s*-\s*(.*)",   caption)
    rarity_match = re.search(r"Rarity\s*-\s*(\d+)", caption)
    price_match  = re.search(r"Price\s*-\s*(\d+)",  caption)

    missing = []
    if not name:          missing.append("Name")
    if not anime:         missing.append("Anime")
    if not rarity_match:  missing.append("Rarity")
    if not price_match:   missing.append("Price")

    if missing:
        await message.reply_text(
            f"❌ Missing fields: {', '.join(missing)}\n\n"
            "Format:\nName - ...\nAnime - ...\nRarity - (number)\nPrice - 83"
        )
        return

    name          = name.group(1).strip()
    anime         = anime.group(1).strip()
    rarity_number = int(rarity_match.group(1))
    price         = int(price_match.group(1))

    # Videos always get Animation rarity
    if reply.video:
        rarity = "🎥 Animation"
    else:
        rarity = rarity_map.get(rarity_number)
        if not rarity:
            await message.reply_text(
                "❌ Invalid rarity number!\n\n"
                + "\n".join([f"{k} - {v}" for k, v in rarity_map.items() if k != 10])
            )
            return

    rarity_emoji = rarity.split(" ")[0]
    rarity_name  = rarity.split(" ", 1)[1]

    # Category tag
    emoji_match   = re.search(r'\[(.*?)\]', name)
    category_line = ""
    if emoji_match:
        emoji = emoji_match.group(1)
        if emoji in CATEGORY_MAP:
            category_line = CATEGORY_MAP[emoji]

    char_id   = await get_next_character_id()
    added_by  = message.from_user.first_name

    final_caption = (
        f"OwO! Check out this character!\n\n"
        f"{anime}\n"
        f"{char_id}: {name}\n\n"
        f"({rarity_emoji} 𝙍𝘼𝙍𝙄𝙏𝙔: {rarity_name})\n"
    )
    if category_line:
        final_caption += f"\n{category_line}\n"
    final_caption += f"\n➼ ᴀᴅᴅᴇᴅ ʙʏ: {added_by}"

    if reply.photo:
        file_id    = reply.photo.file_id
        sent       = await client.send_photo(CHARA_CHANNEL_ID, photo=file_id, caption=final_caption)
        media_type = "photo"
    elif reply.video:
        file_id    = reply.video.file_id
        sent       = await client.send_video(CHARA_CHANNEL_ID, video=file_id, caption=final_caption)
        media_type = "video"
    else:
        await message.reply_text("Reply to a photo or video.")
        return

    await collection.insert_one({
        "id":         char_id,
        "name":       name,
        "anime":      anime,
        "rarity":     rarity,
        "price":      price,
        "img_url":    file_id,
        "type":       media_type,
        "message_id": sent.id,
    })

    await message.reply_text(
        f"✅ Character added!\n\n"
        f"🆔 ID     : {char_id}\n"
        f"👤 Name   : {name}\n"
        f"📺 Anime  : {anime}\n"
        f"✨ Rarity : {rarity}\n"
        f"💰 Price  : {price} Exlix"
    )


# ──────────────────────────────────────────────
#  /delete
# ──────────────────────────────────────────────

@app.on_message(filters.command("delete") & sudo_filter)
async def delete_character(client: Client, message: Message):
    args = message.text.split(maxsplit=1)[1:]
    if len(args) != 1:
        await message.reply_text(capsify("Use: /delete id"))
        return

    character_id = args[0].strip()
    character    = await collection.find_one_and_delete({"id": character_id})

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

    await message.reply_text(
        capsify(
            f"✅ Character Deleted Successfully!\n\n"
            f"🆔 ID: {character_id}\n"
            f"👤 Name: {character.get('name', 'Unknown')}\n"
            f"📺 Anime: {character.get('anime', 'Unknown')}\n"
            f"✨ Rarity: {character.get('rarity', 'Unknown')}\n\n"
            f"🗑 Removed from {len(bulk)} user(s) collection."
        )
    )


# ──────────────────────────────────────────────
#  /update
# ──────────────────────────────────────────────

@app.on_message(filters.command("update") & uploader_filter)
async def update_character(client: Client, message: Message):
    args = message.text.split(maxsplit=3)[1:]
    if len(args) != 3:
        await message.reply_text("Use: /update id field value")
        return

    char_id, field, value = args
    character = await collection.find_one({"id": char_id})
    if not character:
        await message.reply_text("Character not found")
        return

    valid = ["name", "anime", "rarity", "price", "img_url"]
    if field not in valid:
        await message.reply_text("Invalid field")
        return

    if field in ["name", "anime"]:
        value = value.replace("-", " ").title()
    if field == "rarity":
        try:
            value = rarity_map[int(value)]
        except Exception:
            await message.reply_text("Invalid rarity")
            return
    if field == "price":
        try:
            value = int(value)
        except Exception:
            await message.reply_text("Invalid price")
            return

    await collection.update_one({"id": char_id}, {"$set": {field: value}})

    bulk = []
    async for user in user_collection.find():
        if "characters" in user:
            for c in user["characters"]:
                if c["id"] == char_id:
                    c[field] = value
            bulk.append(UpdateOne({"_id": user["_id"]}, {"$set": {"characters": user["characters"]}}))
    if bulk:
        await user_collection.bulk_write(bulk)

    await message.reply_text("Character updated")


# ──────────────────────────────────────────────
#  /r  – quick rarity update
# ──────────────────────────────────────────────

@app.on_message(filters.command("r") & sudo_filter)
async def update_rarity(client: Client, message: Message):
    args = message.text.split(maxsplit=2)[1:]
    if len(args) != 2:
        await message.reply_text("Use: /r id rarity_number")
        return

    char_id, rarity = args
    character = await collection.find_one({"id": char_id})
    if not character:
        await message.reply_text("Character not found")
        return

    try:
        rarity_value = rarity_map[int(rarity)]
    except Exception:
        await message.reply_text("Invalid rarity number")
        return

    await collection.update_one({"id": char_id}, {"$set": {"rarity": rarity_value}})

    bulk = []
    async for user in user_collection.find():
        if "characters" in user:
            for c in user["characters"]:
                if c["id"] == char_id:
                    c["rarity"] = rarity_value
            bulk.append(UpdateOne({"_id": user["_id"]}, {"$set": {"characters": user["characters"]}}))
    if bulk:
        await user_collection.bulk_write(bulk)

    await message.reply_text(f"Rarity updated to {rarity_value}")


# ──────────────────────────────────────────────
#  /arrange
# ──────────────────────────────────────────────

@app.on_message(filters.command("arrange") & sudo_filter)
async def arrange_characters(client: Client, message: Message):
    characters = await collection.find().sort("id", 1).to_list(length=None)
    if not characters:
        await message.reply_text("No characters found")
        return

    old_new = {}
    counter = 1
    bulk    = []

    for char in characters:
        old = char["id"]
        new = str(counter).zfill(2)
        old_new[old] = new
        if old != new:
            bulk.append(UpdateOne({"_id": char["_id"]}, {"$set": {"id": new}}))
        counter += 1

    if bulk:
        await collection.bulk_write(bulk)

    user_bulk = []
    async for user in user_collection.find():
        if "characters" in user:
            for c in user["characters"]:
                if c["id"] in old_new:
                    c["id"] = old_new[c["id"]]
            user_bulk.append(UpdateOne({"_id": user["_id"]}, {"$set": {"characters": user["characters"]}}))
    if user_bulk:
        await user_collection.bulk_write(user_bulk)

    await message.reply_text("Characters rearranged")
        
