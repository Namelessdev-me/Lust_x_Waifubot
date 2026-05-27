from pyrogram import Client, filters
from pyrogram.types import Message
from . import collection, user_collection, app, sudo_filter, capsify
from Lust.config import OWNER_ID


def clean_char(c):
    d = dict(c)
    d.pop('_id', None)
    return d


async def send_char_media(client, chat_id, character, caption, reply_to=None):
    img = character.get('img_url', '')
    char_type = character.get('type', 'photo')
    try:
        if char_type == 'video':
            await client.send_video(chat_id=chat_id, video=img, caption=caption, reply_to_message_id=reply_to)
        else:
            await client.send_photo(chat_id=chat_id, photo=img, caption=caption, reply_to_message_id=reply_to)
    except Exception:
        await client.send_message(chat_id=chat_id, text=caption, reply_to_message_id=reply_to)


def get_target(message, args):
    if message.reply_to_message:
        u = message.reply_to_message.from_user
        return u.id, u.first_name
    if args:
        try:
            return int(args[0]), args[0]
        except ValueError:
            raise ValueError("❌ Invalid user ID.")
    raise ValueError("❌ Reply to a user OR provide user_id.")



@app.on_message(filters.command("addchar") & sudo_filter)
async def addchar_cmd(client: Client, message: Message):
    args = message.text.split()[1:]
    try:
        if message.reply_to_message:
            if not args:
                return await message.reply_text(capsify("Usage: /addchar <char_id> (reply to user)"))
            char_id = str(args[0])
            target_id = message.reply_to_message.from_user.id
            target_name = message.reply_to_message.from_user.first_name
        else:
            if len(args) < 2:
                return await message.reply_text(capsify("Usage: /addchar <user_id> <char_id>"))
            target_id = int(args[0])
            char_id = str(args[1])
            u = await user_collection.find_one({"id": target_id})
            target_name = u.get("first_name", str(target_id)) if u else str(target_id)
    except (ValueError, IndexError):
        return await message.reply_text(capsify("❌ Invalid args."))

    character = await collection.find_one({'id': char_id})
    if not character:
        return await message.reply_text(capsify(f"❌ Character ID {char_id} not found."))

    await user_collection.update_one(
        {'id': target_id},
        {'$push': {'characters': clean_char(character)}}
    )

    caption = (
        f"✅ Character Added!\n\n"
        f"👤 To    : {target_name}\n"
        f"🆔 ID    : {char_id}\n"
        f"📛 Name  : {character['name']}\n"
        f"📺 Anime : {character['anime']}\n"
        f"✨ Rarity: {character.get('rarity', 'Unknown')}"
    )
    await send_char_media(client, message.chat.id, character, capsify(caption), reply_to=message.id)



@app.on_message(filters.command("add") & sudo_filter)
async def add_all_cmd(client: Client, message: Message):
    args = message.text.split()[1:]
    try:
        target_id, target_name = get_target(message, args)
    except ValueError as e:
        return await message.reply_text(capsify(str(e)))

    user = await user_collection.find_one({'id': target_id})
    if not user:
        return await message.reply_text(capsify(f"❌ User {target_id} not found in DB."))

    all_chars = await collection.find({}).to_list(length=None)
    existing = {c['id'] for c in user.get('characters', [])}
    new_chars = [clean_char(c) for c in all_chars if c.get('id') not in existing]

    if not new_chars:
        return await message.reply_text(capsify(f"ℹ️ {target_name} already has all characters."))

    await user_collection.update_one(
        {'id': target_id},
        {'$push': {'characters': {'$each': new_chars}}}
    )

    await message.reply_text(capsify(
        f"✅ All Characters Added!\n\n"
        f"👤 To      : {target_name}\n"
        f"🆔 ID      : {target_id}\n"
        f"➕ Added   : {len(new_chars)} characters\n"
        f"📦 Total   : {len(existing) + len(new_chars)} characters"
    ))



@app.on_message(filters.command("kill") & sudo_filter)
async def kill_cmd(client: Client, message: Message):
    args = message.text.split()[1:]
    try:
        if message.reply_to_message:
            if not args:
                return await message.reply_text(capsify("Usage: /kill <char_id> (reply to user)"))
            char_id = str(args[0])
            target_id = message.reply_to_message.from_user.id
            target_name = message.reply_to_message.from_user.first_name
        else:
            if len(args) < 2:
                return await message.reply_text(capsify("Usage: /kill <user_id> <char_id>"))
            target_id = int(args[0])
            char_id = str(args[1])
            u = await user_collection.find_one({"id": target_id})
            target_name = u.get("first_name", str(target_id)) if u else str(target_id)
    except (ValueError, IndexError):
        return await message.reply_text(capsify("❌ Invalid args."))

    character = await collection.find_one({'id': char_id})
    if not character:
        return await message.reply_text(capsify(f"❌ Character ID {char_id} not found."))

    result = await user_collection.update_one(
        {'id': target_id},
        {'$pull': {'characters': {'id': char_id}}}
    )

    if result.modified_count == 0:
        return await message.reply_text(capsify(f"❌ {target_name} doesn't have character {char_id}."))

    await message.reply_text(capsify(
        f"✅ Character Removed!\n\n"
        f"👤 From  : {target_name}\n"
        f"🆔 ID    : {char_id}\n"
        f"📛 Name  : {character['name']}\n"
        f"📺 Anime : {character['anime']}\n"
        f"✨ Rarity: {character.get('rarity', 'Unknown')}"
    ))



@app.on_message(filters.command("killall") & sudo_filter)
async def killall_cmd(client: Client, message: Message):
    args = message.text.split()[1:]
    try:
        target_id, target_name = get_target(message, args)
    except ValueError as e:
        return await message.reply_text(capsify(str(e)))

    user = await user_collection.find_one({'id': target_id})
    if not user:
        return await message.reply_text(capsify(f"❌ User {target_id} not found."))

    count = len(user.get('characters', []))
    await user_collection.update_one({'id': target_id}, {'$set': {'characters': []}})

    await message.reply_text(capsify(
        f"✅ All Characters Removed!\n\n"
        f"👤 From    : {target_name}\n"
        f"🆔 ID      : {target_id}\n"
        f"🗑 Removed : {count} characters"
    ))




@app.on_message(filters.command("takechar") & filters.user(OWNER_ID))
async def takechar_cmd(client: Client, message: Message):
    args = message.text.split()[1:]
    try:
        if message.reply_to_message:
            if not args:
                return await message.reply_text(capsify("Usage: /takechar <char_id> (reply to user)"))
            char_id = str(args[0])
            target_id = message.reply_to_message.from_user.id
            target_name = message.reply_to_message.from_user.first_name
        else:
            if len(args) < 2:
                return await message.reply_text(capsify("Usage: /takechar <user_id> <char_id>"))
            target_id = int(args[0])
            char_id = str(args[1])
            u = await user_collection.find_one({"id": target_id})
            target_name = u.get("first_name", str(target_id)) if u else str(target_id)
    except (ValueError, IndexError):
        return await message.reply_text(capsify("❌ Invalid args."))

    user = await user_collection.find_one({'id': target_id})
    if not user:
        return await message.reply_text(capsify(f"❌ User {target_id} not found."))

    has_char = any(c.get('id') == char_id for c in user.get('characters', []))
    if not has_char:
        return await message.reply_text(capsify(f"❌ {target_name} doesn't have character {char_id}."))

    await user_collection.update_one(
        {'id': target_id},
        {'$pull': {'characters': {'id': char_id}}}
    )

    character = await collection.find_one({'id': char_id})
    char_name = character['name'] if character else char_id

    await message.reply_text(capsify(
        f"✅ Character Taken!\n\n"
        f"👤 From  : {target_name}\n"
        f"🆔 ID    : {char_id}\n"
        f"📛 Name  : {char_name}\n"
        f"✨ Rarity: {character.get('rarity', 'Unknown') if character else 'Unknown'}"
    ))
