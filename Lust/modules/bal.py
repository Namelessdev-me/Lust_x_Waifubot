import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from . import Lusts as app, user_collection, show, sbank, capsify
from datetime import datetime
from .block import block_dec, temp_block

AUTO_DELETE_SECONDS = 120

async def auto_delete(msg, delay=AUTO_DELETE_SECONDS):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass

@app.on_message(filters.command("bal"))
@block_dec
async def balance(client: Client, message: Message):
    if not message.from_user:
        sent = await message.reply_text(capsify("COULDN'T RETRIEVE USER INFORMATION."))
        asyncio.create_task(auto_delete(sent))
        return

    user_id = message.from_user.id
    username = message.from_user.first_name or "None"

    if temp_block(user_id):
        return

    user_data = await user_collection.find_one(
        {'id': user_id},
        projection={'balance': 1, 'saved_amount': 1, 'loan_amount': 1}
    )

    if user_data:
        ub = await show(user_id)
        balance_amount = int(ub)
        bb = await sbank(user_id)
        saved_amount = int(bb)
        loan_amount = user_data.get('loan_amount', 0)

        total_worth = balance_amount + saved_amount

        caption = "✦━═❖ ᴇʟɪxɪʀ ᴀᴄᴄᴏᴜɴᴛ ❖═━✦\n"
        caption += "╭────────────────────╮\n"
        caption += f"• ɴᴀᴍᴇ     : {username}\n"
        caption += f"• ɪᴅ       : {user_id}\n"
        caption += f"• ᴇʟɪxɪʀ   : {balance_amount:,} ᴇʟɪxɪʀ 💸\n"
        caption += f"• sᴀᴠɪɴɢs  : {saved_amount:,} 💾\n"
        caption += f"• ʟᴏᴀɴ     : {loan_amount:,} 📝\n"
        caption += f"• ᴛᴏᴛᴀʟ ᴡᴏʀᴛʜ : {total_worth:,} 💸\n"
        caption += "╰────────────────────╯\n"
        caption += "✦━═❖ ᴇɴᴊᴏʏ ʏᴏᴜʀ ʜᴜɴᴛ ❖═━✦"

        sent = await message.reply_text(caption)
        asyncio.create_task(auto_delete(sent))
    else:
        error_caption = "✦━═❖ ᴇʟɪxɪʀ ᴀᴄᴄᴏᴜɴᴛ ❖═━✦\n"
        error_caption += "╭────────────────────╮\n"
        error_caption += f"• ɴᴀᴍᴇ     : {username}\n"
        error_caption += f"• ɪᴅ       : {user_id}\n"
        error_caption += "• sᴛᴀᴛᴜs   : ɴᴏᴛ ʀᴇɢɪsᴛᴇʀᴇᴅ ⚠️\n"
        error_caption += "╰────────────────────╯\n"
        error_caption += "✦━═❖ ʀᴇɢɪsᴛᴇʀ ɪɴ ʙᴏᴛ ᴅᴍ ❖═━✦\n\n"
        error_caption += "ᴘʟᴇᴀsᴇ sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ɪɴ ᴅᴍ ᴛᴏ ʀᴇɢɪsᴛᴇʀ."

        sent = await message.reply_text(error_caption)
        asyncio.create_task(auto_delete(sent))
