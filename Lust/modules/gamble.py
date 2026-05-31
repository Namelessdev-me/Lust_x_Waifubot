import asyncio
import random
from pyrogram import Client, filters
from Lust import user_collection
from . import add, deduct, show, abank, dbank, sbank, app, capsify
from .block import block_dec, temp_block

AUTO_DELETE_SECONDS = 120

async def auto_delete(msg, delay=AUTO_DELETE_SECONDS):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass

@app.on_message(filters.command("gamble"))
@block_dec
async def gamble(client, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    user = await user_collection.find_one({'id': user_id})
    balance = int(user.get('balance', 0))

    args = message.text.split()[1:]
    if len(args) != 2:
        sent = await message.reply_text(capsify("Usage: /gamble <amount> <l/r>"))
        asyncio.create_task(auto_delete(sent))
        return

    try:
        amount = int(args[0])
        choice = args[1].lower()
    except ValueError:
        sent = await message.reply_text(capsify("Invalid amount."))
        asyncio.create_task(auto_delete(sent))
        return

    if choice not in ['l', 'r']:
        sent = await message.reply_text(capsify("Invalid choice. Please use /gamble l/r."))
        asyncio.create_task(auto_delete(sent))
        return

    min_bet = int(balance * 0.07)
    if amount < min_bet:
        sent = await message.reply_text(capsify(f"Please gamble at least 7% of your balance, which is {min_bet} Exlix."))
        asyncio.create_task(auto_delete(sent))
        return

    if amount > balance:
        sent = await message.reply_text(capsify(f"You do not have enough balance to gamble {amount} Exlix. Your current balance is {balance} Exlix."))
        asyncio.create_task(auto_delete(sent))
        return

    if random.randint(1, 100) <= 10:
        coin_side = choice
        new_balance = amount
        message_text = capsify(f"🤩 You chose {choice} and won {amount} Exlix.\nCoin was in {coin_side} hand.")
    else:
        coin_side = 'l' if choice == 'r' else 'r'
        new_balance = -amount
        message_text = capsify(f"🥲 You chose {choice} and lost {amount} Exlix.\nCoin was in {coin_side} hand.")

    await add(user_id, new_balance)

    photo_url = "https://telegra.ph/file/889fb66c41a9ead354c59.jpg" if coin_side == choice else "https://telegra.ph/file/99a98f60b22759857056a.jpg"
    sent = await message.reply_photo(photo=photo_url, caption=message_text)
    asyncio.create_task(auto_delete(sent))
