from telegram import Update, InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from Lust import user_collection, collection, application
from . import capsify
from .block import block_dec_ptb


@block_dec_ptb
async def details(update: Update, context: CallbackContext) -> None:
    try:
        args = context.args
        character_id = args[0]
    except (IndexError, ValueError):
        await update.message.reply_text(capsify("Provide a valid character ID"))
        return

    character = await collection.find_one({'id': character_id})

    if not character:
        await update.message.reply_text(capsify("Character not found"))
        return

    global_count = await user_collection.count_documents({'characters.id': character['id']})

    rarity = character.get('rarity', "Unknown")
    price = character.get('price', "Unknown")
    category = character.get('category', "None")
    char_type = character.get("type", "photo")

    caption = f"""
╒═══「 𝗖𝗛𝗔𝗥𝗔𝗖𝗧𝗘𝗥 𝗜𝗡𝗙𝗢 」
╰─➩ ɴᴀᴍᴇ: {character['name']}
╰─➩ ɪᴅ: {character['id']}
╰─➩ ᴀɴɪᴍᴇ: {character['anime']}
╰─➩ ᴄᴀᴛᴇɢᴏʀʏ: {category}
╰─➩ ʀᴀʀɪᴛʏ: {rarity}
╰─➩ ᴘʀɪᴄᴇ: {price} Exlix
╰─➩ ᴏᴡɴᴇᴅ ʙʏ: {global_count} Users
╰──────────────────
"""

    keyboard = [
        [IKB("How many I have ❓", callback_data=f"check_{character_id}")]
    ]
    reply_markup = IKM(keyboard)

    if char_type == "video":
        await update.message.reply_video(
            video=character['img_url'],
            caption=capsify(caption),
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_photo(
            photo=character['img_url'],
            caption=capsify(caption),
            parse_mode='HTML',
            reply_markup=reply_markup
        )


async def check(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    data = query.data  
    parts = data.split('_')

    if len(parts) == 2:
        character_id = parts[1]
    elif len(parts) >= 3:
        character_id = parts[-1]
    else:
        await query.answer(capsify("Invalid data."), show_alert=True)
        return

    user_data = await user_collection.find_one({'id': user_id})

    if user_data:
        characters = user_data.get('characters', [])
        quantity = sum(1 for char in characters if str(char.get('id', '')) == str(character_id))
        await query.answer(
            capsify(f"You have {quantity} of this character."),
            show_alert=True
        )
    else:
        await query.answer(
            capsify("You don't have this character."),
            show_alert=True
        )


application.add_handler(CommandHandler('check', details, block=False))
application.add_handler(CallbackQueryHandler(check, pattern="check_"))
    
