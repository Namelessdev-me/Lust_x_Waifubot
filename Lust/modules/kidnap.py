import random
import time
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from Lust import user_collection, collection, application
from Lust.utils import show, deduct
from .block import block_dec_ptb, block_cbq_ptb
from . import capsify

ENTRY_FEE = 5000
COOLDOWN = 50
ALLOWED_RARITIES = {"🟡 Legendary", "🔮 Limited", "🎐 Devine"}


RARITY_SUCCESS_RATE = {
    "🔮 Limited": 45,  
    "🟡 Legendary": 50, 
    "🎐 Devine": 40,    
}
DEFAULT_SUCCESS_RATE = 50

pending_kidnaps = {}
kidnap_cooldowns = {}


@block_dec_ptb
async def kidnap(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    now = time.time()
    if user_id in kidnap_cooldowns:
        remaining = COOLDOWN - (now - kidnap_cooldowns[user_id])
        if remaining > 0:
            await update.message.reply_text(capsify(f"⏳ Wait {int(remaining)}s before kidnapping again!"))
            return

    if user_id in pending_kidnaps:
        await update.message.reply_text(capsify("❌ You already have an active kidnap attempt!"))
        return

    bal = await show(user_id)
    if bal < ENTRY_FEE:
        await update.message.reply_text(capsify("❌ Insufficient exlic balance!"))
        return

    valid_chars = await collection.find({"rarity": {"$in": list(ALLOWED_RARITIES)}}).to_list(length=None)
    if not valid_chars:
        await update.message.reply_text(capsify("❌ No eligible characters found!"))
        return

    character = random.choice(valid_chars)
    await deduct(user_id, ENTRY_FEE)
    pending_kidnaps[user_id] = character
    kidnap_cooldowns[user_id] = now

    name = character.get('name', 'Unknown')
    anime = character.get('anime', 'Unknown')
    char_id = character.get('id', '???')
    rarity = character.get('rarity', '???')
    img_url = character.get('img_url', '')

    caption = (
        f"{capsify('🌙 A WAIFU IS WALKING ALONE...')}\n\n"
        f"{capsify('♦️ NAME:')} {capsify(name)}\n"
        f"{capsify('🧧 ANIME:')} {capsify(anime)}\n"
        f"{capsify('🆔:')} {char_id}\n"
        f"{capsify('🌟 RARITY:')} {rarity}"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("😈 KIDNAP HER", callback_data=f"kidnap:{user_id}")]
    ])

    try:
        await update.message.reply_photo(photo=img_url, caption=caption, reply_markup=keyboard)
    except Exception:
        await update.message.reply_text(text=caption, reply_markup=keyboard)


@block_cbq_ptb
async def kidnap_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    clicker_id = query.from_user.id
    data = query.data.split(":")

    if len(data) < 2:
        await query.answer("Invalid data!", show_alert=True)
        return

    owner_id = int(data[1])

    if clicker_id != owner_id:
        await query.answer("This isn't your kidnap attempt!", show_alert=True)
        return

    character = pending_kidnaps.pop(owner_id, None)
    if not character:
        await query.answer("This attempt has expired!", show_alert=True)
        return

    name = character.get('name', 'Unknown')
    anime = character.get('anime', 'Unknown')
    char_id = character.get('id', '???')
    rarity = character.get('rarity', '???')


    process_text = (
        f"{capsify('⏳ PROCESS IN PROGRESS.....')}\n\n"
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


    success_rate = RARITY_SUCCESS_RATE.get(rarity, DEFAULT_SUCCESS_RATE)
    success = random.randint(1, 100) <= success_rate

    if success:
        user_data = await user_collection.find_one({'id': owner_id})
        if user_data:
            await user_collection.update_one({'id': owner_id}, {'$push': {'characters': character}})
        else:
            await user_collection.insert_one({'id': owner_id, 'characters': [character]})

        result_text = (
            f"{capsify('😈 YOU KNOCKED HER OUT!')}\n\n"
            f"{capsify('♦️ NAME:')} {capsify(name)}\n"
            f"{capsify('🧧 ANIME:')} {capsify(anime)}\n"
            f"{capsify('🆔:')} {char_id}\n"
            f"{capsify('🌟 RARITY:')} {rarity}\n\n"
            f"{capsify('✅ SUCCESSFULLY KIDNAPPED!')}"
        )
    else:
        result_text = (
            f"{capsify('💀 SHE CRACKED YOUR NUTS AND RAN AWAY!')}\n\n"
            f"{capsify('♦️ NAME:')} {capsify(name)}\n"
            f"{capsify('🧧 ANIME:')} {capsify(anime)}\n"
            f"{capsify('🆔:')} {char_id}\n"
            f"{capsify('🌟 RARITY:')} {rarity}\n\n"
            f"{capsify('😭 SHE RESISTED AND ESCAPED!')}"
        )

    try:
        await query.edit_message_caption(caption=result_text)
    except Exception:
        try:
            await query.edit_message_text(text=result_text)
        except Exception:
            pass


application.add_handler(CommandHandler("kidnap", kidnap))
application.add_handler(CallbackQueryHandler(kidnap_callback, pattern=r"^kidnap:"))
