from pyrogram import filters
from . import db, collection, user_collection, app, sudo_filter, capsify

@app.on_message(sudo_filter & filters.command("transfer"))
async def transfer(_, message):
    args = message.text.split()[1:]
    if len(args) != 2:
        await message.reply_text(capsify('Please provide two valid user IDs for the transfer.'))
        return

    try:
        sender_id = int(args[0])
        receiver_id = int(args[1])
    except ValueError:
        await message.reply_text(capsify('Invalid User IDs provided.'))
        return

    sender = await user_collection.find_one({'id': sender_id})
    receiver = await user_collection.find_one({'id': receiver_id})

    if not sender:
        await message.reply_text(capsify(f'Sender with ID {sender_id} not found.'))
        return

    if not receiver:
        await message.reply_text(capsify(f'Receiver with ID {receiver_id} not found.'))
        return

    receiver_slaves = receiver.get('characters', [])
    receiver_slaves.extend(sender.get('characters', []))

    await user_collection.update_one({'id': receiver_id}, {'$set': {'characters': receiver_slaves}})
    await user_collection.update_one({'id': sender_id}, {'$set': {'characters': []}})

    await message.reply_text(capsify('All slaves transferred successfully!'))