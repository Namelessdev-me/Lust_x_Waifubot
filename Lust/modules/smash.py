import asyncio
import random
import time
from pyrogram import filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Lust import user_collection, collection, application
from . import capsify
from .block import block_dec, block_cbq  # <-- confirm these names in block.py, dropped _ptb suffix

COOLDOWN = 900

pending_smash = {}
smash_cooldowns = {}


@block_dec
async def smash(client, message):
    user_id = message.from_user.id

    now = time.time()
    if user_id in smash_cooldowns:
        remaining = COOLDOWN - (now - smash_cooldowns[user_id])
        if remaining > 0:
            await message.reply_text(
                capsify(f"⏳ Chill bro! Wait {int(remaining)}s before smashing again!")
            )
            return

    if user_id in pending_smash:
        await message.reply_text(capsify("❌ You already have an active smash attempt!"))
        return

    video_chars = await collection.find({"rarity": "🎥 Animation"}).to_list(length=None)
    if not video_chars:
        await message.reply_text(capsify("❌ No animation characters found in database!"))
        return

    character = random.choice(video_chars)
    pending_smash[user_id] = character
    smash_cooldowns[user_id] = now

    name = character.get("name", "Unknown")
    anime = character.get("anime", "Unknown")
    char_id = character.get("id", "???")
    rarity = character.get("rarity", "???")
    file_id = character.get("img_url", "")

    caption = (
        f"{capsify('🎥 AN ANIMATION WAIFU APPEARED...')}\n\n"
        f"{capsify('♦️ NAME:')} {capsify(name)}\n"
        f"{capsify('🧧 ANIME:')} {capsify(anime)}\n"
        f"{capsify('🆔:')} {char_id}\n"
        f"{capsify('🌟 RARITY:')} {rarity}\n\n"
        f"{capsify('💦 DO YOU DARE TO SMASH?')}"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💦 SMASH", callback_data=f"smash:{user_id}")]
    ])

    try:
        await message.reply_video(video=file_id, caption=caption, reply_markup=keyboard)
    except Exception:
        try:
            await message.reply_text(text=caption, reply_markup=keyboard)
        except Exception as e:
            await message.reply_text(capsify(f"❌ Error: {e}"))


@block_cbq
async def smash_callback(client, callback_query):
    clicker_id = callback_query.from_user.id
    data = callback_query.data.split(":")

    if len(data) < 2:
        await callback_query.answer("Invalid data!", show_alert=True)
        return

    owner_id = int(data[1])

    if clicker_id != owner_id:
        await callback_query.answer("This isn't your smash attempt!", show_alert=True)
        return

    character = pending_smash.pop(owner_id, None)
    if not character:
        await callback_query.answer("This attempt has expired!", show_alert=True)
        return

    name = character.get("name", "Unknown")
    anime = character.get("anime", "Unknown")
    char_id = character.get("id", "???")
    rarity = character.get("rarity", "???")

    process_text = (
        f"{capsify('⏳ GETTING IN THE MOOD.....')}\n\n"
        f"{capsify('♦️ NAME:')} {capsify(name)}\n"
        f"{capsify('🧧 ANIME:')} {capsify(anime)}\n"
        f"{capsify('🆔:')} {char_id}\n"
        f"{capsify('🌟 RARITY:')} {rarity}"
    )

    try:
        await callback_query.edit_message_caption(caption=process_text, reply_markup=None)
    except Exception:
        try:
            await callback_query.edit_message_text(text=process_text, reply_markup=None)
        except Exception:
            pass

    await callback_query.answer()
    await asyncio.sleep(2)

    success = random.randint(1, 100) <= 35

    if success:
        user_data = await user_collection.find_one({"id": owner_id})
        if user_data:
            await user_collection.update_one({"id": owner_id}, {"$push": {"characters": character}})
        else:
            await user_collection.insert_one({"id": owner_id, "characters": [character]})

        result_text = (
            f"{capsify('😏 YOU SMASHED HER GOOD!')}\n\n"
            f"{capsify('♦️ NAME:')} {capsify(name)}\n"
            f"{capsify('🧧 ANIME:')} {capsify(anime)}\n"
            f"{capsify('🆔:')} {char_id}\n"
            f"{capsify('🌟 RARITY:')} {rarity}\n\n"
            f"{capsify('✅ WAIFU ADDED TO YOUR COLLECTION!')}"
        )
    else:
        result_text = (
            f"{capsify('💀 SHE REJECTED YOU HARD!')}\n\n"
            f"{capsify('♦️ NAME:')} {capsify(name)}\n"
            f"{capsify('🧧 ANIME:')} {capsify(anime)}\n"
            f"{capsify('🆔:')} {char_id}\n"
            f"{capsify('🌟 RARITY:')} {rarity}\n\n"
            f"{capsify('😭 YOU FAILED TO SCORE. BETTER LUCK NEXT TIME!')}"
        )

    try:
        await callback_query.edit_message_caption(caption=result_text)
    except Exception:
        try:
            await callback_query.edit_message_text(text=result_text)
        except Exception:
            pass


application.add_handler(MessageHandler(smash, filters.command("smash")))
application.add_handler(CallbackQueryHandler(smash_callback, filters.regex(r"^smash:")))
