import asyncio
import random
import time
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext
from Lust import user_collection, collection, application
from . import capsify
from .block import block_dec_ptb, block_cbq_ptb

COOLDOWN = 900

pending_charm = {}
charm_cooldowns = {}


@block_dec_ptb
async def charm(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    now = time.time()
    if user_id in charm_cooldowns:
        remaining = COOLDOWN - (now - charm_cooldowns[user_id])
        if remaining > 0:
            await update.message.reply_text(
                capsify(f"⏳ Chill bro! Wait {int(remaining)}s before trying again!")
            )
            return

    if user_id in pending_charm:
        await update.message.reply_text(capsify("❌ You already have an active charm attempt!"))
        return

    video_chars = await collection.find({"rarity": "🎥 Animation"}).to_list(length=None)
    if not video_chars:
        await update.message.reply_text(capsify("❌ No animation characters found in database!"))
        return

    character = random.choice(video_chars)
    pending_charm[user_id] = character
    charm_cooldowns[user_id] = now

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
        f"{capsify('💘 WILL YOU TRY TO CHARM HER?')}"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💘 CHARM", callback_data=f"charm:{user_id}")]
    ])

    try:
        await update.message.reply_video(video=file_id, caption=caption, reply_markup=keyboard)
    except Exception:
        try:
            await update.message.reply_text(text=caption, reply_markup=keyboard)
        except Exception as e:
            await update.message.reply_text(capsify(f"❌ Error: {e}"))


@block_cbq_ptb
async def charm_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    clicker_id = query.from_user.id
    data = query.data.split(":")

    if len(data) < 2:
        await query.answer("Invalid data!", show_alert=True)
        return

    owner_id = int(data[1])

    if clicker_id != owner_id:
        await query.answer("This isn't your charm attempt!", show_alert=True)
        return

    character = pending_charm.pop(owner_id, None)
    if not character:
        await query.answer("This attempt has expired!", show_alert=True)
        return

    name = character.get("name", "Unknown")
    anime = character.get("anime", "Unknown")
    char_id = character.get("id", "???")
    rarity = character.get("rarity", "???")

    process_text = (
        f"{capsify('⏳ MAKING YOUR MOVE.....')}\n\n"
        f"{capsify('♦️ NAME:')} {capsify(name)}\n"
        f"{capsify('🧧 ANIME:')} {capsify(anime)}\n"
        f"{capsify('🆔:')} {char_id}\n"
        f"{capsify('🌟 RARITY:')} {rarity}"
    )

    try:
        await query.edit_message_caption(caption=process_text, reply_markup=None)
    except Exception:
        try:
            await query.edit_message_text(text=process_text, reply_markup=None)
        except Exception:
            pass

    await query.answer()
    await asyncio.sleep(2)

    success = random.randint(1, 100) <= 35

    if success:
        user_data = await user_collection.find_one({"id": owner_id})
        if user_data:
            await user_collection.update_one({"id": owner_id}, {"$push": {"characters": character}})
        else:
            await user_collection.insert_one({"id": owner_id, "characters": [character]})

        result_text = (
            f"{capsify('😏 YOU WON HER OVER!')}\n\n"
            f"{capsify('♦️ NAME:')} {capsify(name)}\n"
            f"{capsify('🧧 ANIME:')} {capsify(anime)}\n"
            f"{capsify('🆔:')} {char_id}\n"
            f"{capsify('🌟 RARITY:')} {rarity}\n\n"
            f"{capsify('✅ WAIFU ADDED TO YOUR COLLECTION!')}"
        )
    else:
        result_text = (
            f"{capsify('💀 SHE WASN'T INTERESTED!')}\n\n"
            f"{capsify('♦️ NAME:')} {capsify(name)}\n"
            f"{capsify('🧧 ANIME:')} {capsify(anime)}\n"
            f"{capsify('🆔:')} {char_id}\n"
            f"{capsify('🌟 RARITY:')} {rarity}\n\n"
            f"{capsify('😭 YOU FAILED TO IMPRESS HER. BETTER LUCK NEXT TIME!')}"
        )

    try:
        await query.edit_message_caption(caption=result_text)
    except Exception:
        try:
            await query.edit_message_text(text=result_text)
        except Exception:
            pass


application.add_handler(CommandHandler("charm", charm))
application.add_handler(CallbackQueryHandler(charm_callback, pattern=r"^charm:"))
