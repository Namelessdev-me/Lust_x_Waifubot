from telegram import Update, InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from Lust import user_collection, collection, application
from . import capsify
from .block import block_dec_ptb
import asyncio


def build_caption(character, global_count):
    rarity = character.get('rarity', "Unknown")
    price = character.get('price', "Unknown")
    category = character.get('category', "None")

    caption = f"""
╒═══「 ᴄʜᴀʀᴀᴄᴛᴇʀ ᴘʀᴏꜰɪʟᴇ 」═══╕
│
╰─➤ 𝗡𝗔𝗠𝗘   ›  {character['name']}
╰─➤ 𝗜𝗗     ›  {character['id']}
╰─➤ 𝗔𝗡𝗜𝗠𝗘  ›  {character['anime']}
╰─➤ 𝗧𝗬𝗣𝗘   ›  {category}
╰─➤ 𝗥𝗔𝗥𝗜𝗧𝗬 ›  {rarity}
╰─➤ 𝗣𝗥𝗜𝗖𝗘  ›  {price} 𝗘𝘅𝗹𝗶𝘅
╰─➤ 𝗢𝗪𝗡𝗘𝗗  ›  {global_count} 𝗨𝘀𝗲𝗿𝘀
│
╘═══────────────────────═══╛"""
    return caption


def build_top_caption(top_users, character_name):
    lines = [
        f"╒═══「 𝗧𝗢𝗣 𝗛𝗢𝗟𝗗𝗘𝗥𝗦 」═══╕",
        f"│  ᴄʜᴀʀ › {character_name}",
        f"╞═══────────────────────═══╡"
    ]
    medals = ["🥇", "🥈", "🥉"]
    for i, user in enumerate(top_users, 1):
        name = user.get('first_name', 'Unknown')
        username = user.get('username')
        count = user.get('count', 0)
        display = f"@{username}" if username else name
        medal = medals[i - 1] if i <= 3 else f"{i}."
        lines.append(f"╰─➤ {medal}  {display}  ›  {count}ˣ")
    lines.append("╘═══────────────────────═══╛")
    return "\n".join(lines)


async def auto_delete(message, delay: int):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass


@block_dec_ptb
async def check(update: Update, context: CallbackContext) -> None:
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
    char_type = character.get("type", "photo")
    caption = build_caption(character, global_count)

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


async def top_holders(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data
    character_id = data.split('_', 1)[1]

    character = await collection.find_one({'id': character_id})
    if not character:
        await query.answer(capsify("Character not found."), show_alert=True)
        return

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
        keyboard = [[IKB("⬅️ Back", callback_data=f"back_{character_id}")]]
        await query.edit_message_caption(
            caption=text,
            parse_mode='HTML',
            reply_markup=IKM(keyboard)
        )
        return

    text = capsify(build_top_caption(top_users, character.get('name', '')))
    keyboard = [[IKB("⬅️ Back", callback_data=f"back_{character_id}")]]

    await query.edit_message_caption(
        caption=text,
        parse_mode='HTML',
        reply_markup=IKM(keyboard)
    )


async def back_to_details(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data
    character_id = data.split('_', 1)[1]

    character = await collection.find_one({'id': character_id})

    if not character:
        await query.answer(capsify("Character not found."), show_alert=True)
        return

    global_count = await user_collection.count_documents({'characters.id': character['id']})
    caption = build_caption(character, global_count)

    keyboard = [
        [IKB("Who Has It 👥", callback_data=f"top_{character_id}")]
    ]

    await query.edit_message_caption(
        caption=capsify(caption),
        parse_mode='HTML',
        reply_markup=IKM(keyboard)
    )


application.add_handler(CommandHandler('check', check, block=False))
application.add_handler(CallbackQueryHandler(top_holders, pattern=r"^top_"))
application.add_handler(CallbackQueryHandler(back_to_details, pattern=r"^back_"))
