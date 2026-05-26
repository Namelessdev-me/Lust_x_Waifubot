from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import UpdateOne
import re

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
9: "💦 Wet"
}


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

    if not reply or not reply.caption:
        await message.reply_text("Reply to photo/video with caption.")
        return


    caption = reply.caption

    try:
        name = re.search(r"Name\s*-\s*(.*)", caption).group(1)
        anime = re.search(r"Anime\s*-\s*(.*)", caption).group(1)
        rarity_number = int(re.search(r"Rarity\s*-\s*(\d+)", caption).group(1))
        price = int(re.search(r"Price\s*-\s*(\d+)", caption).group(1))
    except:
        await message.reply_text("Invalid caption format.")
        return


    rarity = rarity_map.get(rarity_number)

    rarity_emoji = rarity.split(" ")[0]
    rarity_name = rarity.split(" ",1)[1]


    emoji_match = re.search(r'\[(.*?)\]', name)

    category_line = ""

    if emoji_match:
        emoji = emoji_match.group(1)

        if emoji in CATEGORY_MAP:
            category_line = CATEGORY_MAP[emoji]


    char_id = await get_next_character_id()

    added_by = message.from_user.first_name


    final_caption = f"""OwO! Check out this character!

{anime}
{char_id}: {name}

({rarity_emoji} 𝙍𝘼𝙍𝙄𝙏𝙔: {rarity_name})
"""


    if category_line:
        final_caption += f"\n{category_line}\n"


    final_caption += f"\n➼ ᴀᴅᴅᴇᴅ ʙʏ: {added_by}"


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
        "price": price,
        "img_url": file_id,
        "type": media_type,
        "message_id": sent.id
    })


    await message.reply_text(f"Character added with ID {char_id}")



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

    # Delete from channel
    try:
        await client.delete_messages(CHARA_CHANNEL_ID, character["message_id"])
    except Exception:
        pass

    # Remove from all users' collections
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
    valid=["name","anime","rarity","price","img_url"]
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
    await message.reply_text("Rarity updated")

@app.on_message(filters.command("arrange") & sudo_filter)
async def arrange_characters(client: Client, message: Message):
    characters=await collection.find().sort("id",1).to_list(length=None)
    if not characters:
        await message.reply_text("No characters found")
        return
    old_new={}
    counter=1
    bulk=[]
    for char in characters:
        old=char["id"]
        new=str(counter).zfill(2)
        old_new[old]=new
        if old!=new:
            bulk.append(UpdateOne({"_id":char["_id"]},{"$set":{"id":new}}))
        counter+=1
    if bulk:
        await collection.bulk_write(bulk)
    user_bulk=[]
    async for user in user_collection.find():
        if "characters" in user:
            for c in user["characters"]:
                if c["id"] in old_new:
                    c["id"]=old_new[c["id"]]
            user_bulk.append(UpdateOne({"_id":user["_id"]},{"$set":{"characters":user["characters"]}}))
    if user_bulk:
        await user_collection.bulk_write(user_bulk)
    await message.reply_text("Characters rearranged")
    
