import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, Message, CallbackQuery

from . import user_collection, app, capsify
from .block import block_dec, block_cbq, temp_block

AUTO_DELETE_SECONDS = 120  # 2 minutes

async def auto_delete(msg, delay=AUTO_DELETE_SECONDS):
    """Delete a message after `delay` seconds."""
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass

@app.on_message(filters.command("fav"))
@block_dec
async def fav(client: Client, message: Message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    if len(message.command) < 2:
        sent = await message.reply_text(capsify('Please provide Slave ID...'))
        asyncio.create_task(auto_delete(sent))
        return

    character_id = message.command[1]
    user = await user_collection.find_one({'id': user_id})
    if not user:
        sent = await message.reply_text(capsify('You have not got any Slave yet...'))
        asyncio.create_task(auto_delete(sent))
        return

    character = next((c for c in user['characters'] if c['id'] == character_id), None)
    if not character:
        sent = await message.reply_text(capsify('This slave is not in your list'))
        asyncio.create_task(auto_delete(sent))
        return

    if message.chat.id == -1002225496870:
        await handle_confirmation(user_id, character_id, character)
    else:
        keyboard = IKM(
            [
                [IKB(capsify("INLINE"), switch_inline_query_current_chat=f"{character_id}")],
                [
                    IKB(capsify("CONFIRM"), callback_data=f'confirm_{user_id}_{character_id}'),
                    IKB(capsify("CANCEL"), callback_data=f'cancel_{user_id}_{character_id}')
                ]
            ]
        )
        sent = await message.reply_text(capsify(f'Do you want to make {character["name"]} your favorite slave?'), reply_markup=keyboard)
        asyncio.create_task(auto_delete(sent))

async def handle_confirmation(user_id, character_id, character=None):
    if character:
        user = await user_collection.find_one({'id': user_id})
        if user:
            user['favorites'] = [character_id]
            await user_collection.update_one({'id': user_id}, {'$set': {'favorites': user['favorites']}})
            sent = await app.send_message(user_id, capsify(f'Slave {character["name"]} is your favorite now...'))
            asyncio.create_task(auto_delete(sent))
    else:
        sent = await app.send_message(user_id, capsify('You have not got any slave yet...'))
        asyncio.create_task(auto_delete(sent))

@app.on_callback_query(filters.regex(r'^(confirm_|cancel_)'))
@block_cbq
async def button(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data
    action, cmd_user_id, character_id = data.split('_')

    if int(cmd_user_id) != user_id:
        await callback_query.answer("This is not for you baka ❗", show_alert=True)
        return

    if callback_query.message.chat.id == -1002225496870:
        if action == "confirm":
            await handle_confirmation(user_id, character_id)
        else:
            await callback_query.message.edit_text(capsify('Operation canceled.'))
    else:
        if action == "confirm":
            user = await user_collection.find_one({'id': user_id})
            if user:
                character = next((c for c in user['characters'] if c['id'] == character_id), None)
                if character:
                    user['favorites'] = [character_id]
                    await user_collection.update_one({'id': user_id}, {'$set': {'favorites': user['favorites']}})
                    await callback_query.message.edit_text(capsify(f'Slave {character["name"]} is your favorite now...'))
                else:
                    await callback_query.message.edit_text(capsify('This slave is not in your list'))
            else:
                await callback_query.message.edit_text(capsify('You have not got any slave yet...'))
        elif action == "cancel":
            await callback_query.message.edit_text(capsify('Operation canceled.'))
