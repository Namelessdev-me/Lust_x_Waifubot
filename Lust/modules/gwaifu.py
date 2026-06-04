import asyncio
import secrets
import string
from pyrogram import Client, filters
from pyrogram.types import Message
from . import app, collection, capsify
from Lust import db
from Lust.utils import ac
from Lust.utils.sudo import dev_filter
from .block import block_dec, temp_block

codes_collection = db.redeem_codes


def generate_code(length=12):
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


@app.on_message(filters.command("gwaifu") & dev_filter)
@block_dec
async def gwaifu_generate(client: Client, message: Message):
    user_id = message.from_user.id

    if temp_block(user_id):
        return

    args = message.command[1:]
    if len(args) != 2:
        await message.reply_text(
            capsify("📝 Usage: /gwaifu <character_id> <quantity>\nExample: /gwaifu 737 15"),
            quote=True
        )
        return

    char_id_raw, qty_raw = args

    try:
        quantity = int(qty_raw)
        if quantity < 1 or quantity > 100:
            raise ValueError
    except ValueError:
        await message.reply_text(capsify("❌ Quantity must be a number between 1 and 100."), quote=True)
        return

    char_id = str(char_id_raw).zfill(2)
    character = await collection.find_one({'id': char_id})
    if not character:
        await message.reply_text(capsify(f"❌ No character found with ID: {char_id}"), quote=True)
        return

    while True:
        code = generate_code()
        if not await codes_collection.find_one({'code': code}):
            break

    await codes_collection.insert_one({
        'code': code,
        'character_id': char_id,
        'quantity': quantity,
        'used_by': [],
        'created_by': user_id,
        'active': True
    })

    await message.reply_text(
        capsify(f"✅ Redeem Code Generated!\n\n"
                f"🎫 Code      : {code}\n"
                f"👤 Character : {character['name']}\n"
                f"📺 Anime     : {character['anime']}\n"
                f"✨ Rarity    : {character['rarity']}\n"
                f"🆔 Char ID   : {char_id}\n"
                f"📦 Quantity  : x{quantity}\n\n"
                f"Share this code so users can redeem with /gredeem {code}"),
        quote=True
    )


@app.on_message(filters.command("gredeem"))
@block_dec
async def gredeem_code(client: Client, message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    if temp_block(user_id):
        return

    args = message.command[1:]
    if not args:
        await message.reply_text(
            capsify("📝 Usage: /gredeem <code>\nExample: /gredeem ABC123XYZ456"),
            quote=True
        )
        return

    code = args[0].upper().strip()
    code_data = await codes_collection.find_one({'code': code})

    if not code_data:
        await message.reply_text(capsify("❌ Invalid redeem code. Please check and try again."), quote=True)
        return

    if not code_data.get('active', True):
        await message.reply_text(capsify("❌ This redeem code has been deactivated."), quote=True)
        return

    if user_id in code_data.get('used_by', []):
        await message.reply_text(capsify("❌ You have already redeemed this code."), quote=True)
        return

    char_id = code_data['character_id']
    quantity = code_data.get('quantity', 1)

    character = await collection.find_one({'id': char_id})
    if not character:
        await message.reply_text(capsify("❌ The character linked to this code no longer exists."), quote=True)
        return

    for _ in range(quantity):
        await ac(user_id, char_id)

    await codes_collection.update_one(
        {'code': code},
        {'$addToSet': {'used_by': user_id}}
    )

    caption = capsify(
        f"🎉 Redeemed Successfully!\n\n"
        f"Hey {first_name}! You received:\n\n"
        f"👤 {character['name']}\n"
        f"📺 {character['anime']}\n"
        f"✨ {character['rarity']}\n"
        f"🆔 ID: {char_id}\n"
        f"📦 x{quantity} added to your harem!\n\n"
        f"Use /myslaves to view your collection."
    )

    try:
        if character.get('type') == 'video':
            await app.send_video(
                message.chat.id,
                video=character['img_url'],
                caption=caption,
                reply_to_message_id=message.id
            )
        else:
            await app.send_photo(
                message.chat.id,
                photo=character['img_url'],
                caption=caption,
                reply_to_message_id=message.id
            )
    except Exception:
        await message.reply_text(
            capsify(f"🎉 Redeemed! {character['name']} ({character['rarity']}) x{quantity} added to your harem!"),
            quote=True
        )

