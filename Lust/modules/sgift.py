from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext
from Lust import user_collection, application
from .block import block_dec_ptb, block_cbq_ptb
from . import capsify


async def safe_edit(msg, text):
    try:
        await msg.edit_text(text)
    except:
        try:
            await msg.edit_caption(caption=text)
        except:
            pass


@block_dec_ptb
async def gift(update: Update, context: CallbackContext):
    message = update.message
    sender_id = message.from_user.id

    if not message.reply_to_message:
        await message.reply_text(capsify("Reply to a user to gift a character!"))
        return

    receiver_id = message.reply_to_message.from_user.id

    if sender_id == receiver_id:
        await message.reply_text(capsify("You can't gift a character to yourself!"))
        return

    if not context.args or len(context.args) != 1:
        await message.reply_text(capsify("Provide a character ID!"))
        return

    character_id = context.args[0]
    sender = await user_collection.find_one({'id': sender_id})

    if not sender:
        await message.reply_text(capsify("You don't have any characters!"))
        return

    character = next((c for c in sender.get('characters', []) if str(c.get('id')) == str(character_id)), None)

    if not character:
        await message.reply_text(capsify(f"You don't have character {character_id}!"))
        return

    msg_text = (f"{capsify('🎁 CONFIRM GIFTING')}\n\n"
                f"{capsify('♦️ NAME:')} {capsify(character['name'])}\n"
                f"{capsify('🧧 ANIME:')} {capsify(character['anime'])}\n"
                f"{capsify('🆔:')} {character['id']}\n"
                f"{capsify('🌟:')} {character.get('rarity', '🔮 LIMITED')}")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ CONFIRM", callback_data=f"con_gift:{sender_id}:{character_id}:{receiver_id}"),
         InlineKeyboardButton("❌ CANCEL", callback_data=f"can_gift:{sender_id}")]
    ])

    await message.reply_text(msg_text, reply_markup=keyboard)


@block_cbq_ptb
async def gift_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    data = query.data.split(":", 3)
    action = data[0]
    sender_id = int(data[1])

    if query.from_user.id != sender_id:
        await query.answer("This is not for you!", show_alert=True)
        return

    if action == "can_gift":
        await safe_edit(query.message, capsify("❌ GIFT CANCELED"))
        return

    if action == "con_gift":
        if len(data) < 4:
            await query.answer("Invalid data!", show_alert=True)
            return

        character_id = data[2]
        receiver_id = int(data[3])

        sender = await user_collection.find_one({'id': sender_id})
        if not sender:
            await query.answer("Your data not found!", show_alert=True)
            return

        character = next((c for c in sender.get('characters', []) if str(c.get('id')) == str(character_id)), None)
        if not character:
            await query.answer("Character not found in your collection!", show_alert=True)
            await safe_edit(query.message, capsify("❌ CHARACTER NOT FOUND"))
            return

        new_sender_chars = [c for c in sender.get('characters', []) if str(c['id']) != str(character_id)]
        if len(new_sender_chars) == len(sender.get('characters', [])):
            await query.answer("Character already gifted!", show_alert=True)
            return

        await user_collection.update_one({'id': sender_id}, {'$set': {'characters': new_sender_chars}})

        receiver = await user_collection.find_one({'id': receiver_id})
        if receiver:
            await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': character}})
        else:
            await user_collection.insert_one({'id': receiver_id, 'characters': [character]})

        success_msg = (f"{capsify('🎁 GIFT SENT SUCCESSFULLY')}\n\n"
                       f"{capsify('♦️ NAME:')} {capsify(character['name'])}\n"
                       f"{capsify('🧧 ANIME:')} {capsify(character['anime'])}\n"
                       f"{capsify('🆔:')} {character['id']}\n"
                       f"{capsify('🌟:')} {character.get('rarity', '🔮 LIMITED')}")

        await safe_edit(query.message, success_msg)


application.add_handler(CommandHandler("gift", gift))
        
