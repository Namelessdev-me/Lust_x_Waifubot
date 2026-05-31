from telegram import Update, InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from Lust import user_collection, collection, application
from . import capsify
from .block import block_dec_ptb
import asyncio


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
        [IKB("Who Has It 👥", callback_data=f"top_{character_id}")]
    ]
    reply_markup = IKM(keyboard)

    if char_type == "video":
        sent = await update.message.reply_video(
            video=character['img_url'],
            caption=capsify(caption),
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    else:
        sent = await update.message.reply_photo(
            photo=character['img_url'],
            caption=capsify(caption),
            parse_mode='HTML',
            reply_markup=reply_markup
        )


    asyncio.create_task(auto_delete(sent, 120))


async def auto_delete(message, delay: int):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass


async def top_holders(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split('_')
    character_id = parts[-1]


    pipeline = [
        {"$match": {"characters.id": character_id}},
        {"$project": {
            "id": 1,
            "first_name": 1,
            "username": 1,
            "count": {
                "$size": {
                    "$filter": {
                        "input": "$characters",
                        "as": "c",
                        "cond": {"$eq": ["$$c.id", character_id]}
                    }
                }
            }
        }},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]

    top_users = await user_collection.aggregate(pipeline).to_list(length=10)

    if not top_users:
        text = capsify("No one owns this character yet.")
    else:
        lines = [capsify("🏆 Top 10 Holders\n")]
        for i, user in enumerate(top_users, 1):
            name = user.get('first_name', 'Unknown')
            username = user.get('username')
            count = user.get('count', 0)
            if username:
                display = f"@{username}"
            else:
                display = name
            lines.append(f"{i}. {display} — {count}x")
        text = capsify("\n".join(lines))

    keyboard = [
        [IKB("⬅️ Back", callback_data=f"back_{character_id}")]
    ]
    reply_markup = IKM(keyboard)

    await query.edit_message_caption(
        caption=text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )


async def back_to_details(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split('_')
    character_id = parts[-1]

    character = await collection.find_one({'id': character_id})

    if not character:
        await query.answer(capsify("Character not found."), show_alert=True)
        return

    global_count = await user_collection.count_documents({'characters.id': character['id']})

    rarity = character.get('rarity', "Unknown")
    price = character.get('price', "Unknown")
    category = character.get('category', "None")

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
        [IKB("Who Has It 👥", callback_data=f"top_{character_id}")]
    ]
    reply_markup = IKM(keyboard)

    await query.edit_message_caption(
        caption=capsify(caption),
        parse_mode='HTML',
        reply_markup=reply_markup
    )


application.add_handler(CommandHandler('check', details, block=False))
application.add_handler(CallbackQueryHandler(top_holders, pattern=r"^top_"))
application.add_handler(CallbackQueryHandler(back_to_details, pattern=r"^back_"))
