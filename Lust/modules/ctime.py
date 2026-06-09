from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message
from pymongo import ReturnDocument
from . import sudo_filter, app
from Lust import group_user_totals_collection


async def is_sudo(client: Client, user_id: int) -> bool:
    from . import sudb
    user = await sudb.find_one({"id": user_id})
    return user is not None


@app.on_message(filters.command("changetime"))
async def change_time(client: Client, message: Message):
    try:
        user = await app.get_chat_member(message.chat.id, message.from_user.id)
        if user.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await message.reply_text('You do not have permission to use this command.')
            return

        args = message.text.split(maxsplit=1)[1:]
        if len(args) != 1 or not args[0].isdigit():
            await message.reply_text('Incorrect format. Please use: /changetime NUMBER')
            return

        new_frequency = int(args[0])

        if new_frequency < 1:
            await message.reply_text('The message frequency must be at least 1.')
            return
        if new_frequency > 10000:
            await message.reply_text('The message frequency must be below 10,000.')
            return

        sudo = await is_sudo(client, message.from_user.id)
        if not sudo and new_frequency < 100:
            await message.reply_text('You can only set the frequency to 100 or above. Only sudo users can set it below 100.')
            return

        await group_user_totals_collection.find_one_and_update(
            {'chat_id': message.chat.id},
            {'$set': {'message_frequency': new_frequency}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        await message.reply_text(f'Successfully changed character appearance frequency to every {new_frequency} messages.')
    except Exception as e:
        await message.reply_text(f'Failed to change character appearance frequency. Error: {str(e)}')


@app.on_message(filters.command("ctime") & sudo_filter)
async def change_time_sudo(client: Client, message: Message):
    try:
        args = message.text.split(maxsplit=1)[1:]
        if len(args) != 1 or not args[0].isdigit():
            await message.reply_text('Incorrect format. Please use: /ctime NUMBER')
            return

        new_frequency = int(args[0])
        if new_frequency < 1:
            await message.reply_text('The message frequency must be greater than or equal to 1.')
            return
        if new_frequency > 10000:
            await message.reply_text('The message frequency must be below 10,000.')
            return

        await group_user_totals_collection.find_one_and_update(
            {'chat_id': message.chat.id},
            {'$set': {'message_frequency': new_frequency}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        await message.reply_text(f'Successfully changed character appearance frequency to every {new_frequency} messages.')
    except Exception as e:
        await message.reply_text(f'Failed to change character appearance frequency. Error: {str(e)}')
        
