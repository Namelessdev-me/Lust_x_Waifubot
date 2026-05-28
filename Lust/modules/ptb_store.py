from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, InputMediaPhoto as IMP
from datetime import datetime as dt
import random
from . import app, db, add, deduct, show, collection, user_collection, capsify
from .block import block_dec, temp_block, block_cbq

sdb = db.new_store
user_db = db.bought


def today():
    return str(dt.now()).split()[0]


async def get_character(id):
    character = await collection.find_one({"id": str(id)})
    if not character:
        try:
            character = await collection.find_one({"id": int(id)})
        except (ValueError, TypeError):
            pass
    if not character:
        raise ValueError(capsify(f"character with id {id} not found."))
    return character


async def get_available_characters():
    characters = await collection.find().to_list(None)
    return characters


async def get_user_session(user_id: int):
    record = await sdb.find_one({"id": user_id})
    return record["data"] if record else None


async def update_user_session(user_id: int, data):
    await sdb.update_one({"id": user_id}, {"$set": {"data": data}}, upsert=True)


async def clear_user_session(user_id: int):
    await sdb.delete_one({"id": user_id})


async def update_user_bought(user_id: int, data):
    await user_db.update_one({"id": user_id}, {"$set": {"data": data}}, upsert=True)


async def get_user_bought(user_id: int):
    record = await user_db.find_one({"id": user_id})
    return record["data"] if record else None


async def format_character_info(character):
    if not character:
        raise ValueError(capsify("invalid character data."))
    return (
        character["img_url"],
        capsify(
            f"**Name:** {character['name']}\n"
            f"**Anime:** {character['anime']}\n"
            f"**ID:** {character['id']}\n"
            f"**Rarity:** {character['rarity']}\n"
            f"**Price:** {character['price']} Exlix"
        ),
    )


@app.on_message(filters.command(["store", "shop", "market"]))
@block_dec
async def store_handler(_, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    session = await get_user_session(user_id)
    if not session or session[0] != today():
        characters = await get_available_characters()
        if len(characters) < 3:
            return await message.reply_text(capsify("not enough characters in database!"))
        selected_ids = random.sample([c["id"] for c in characters], 3)
        await update_user_session(user_id, [today(), selected_ids])
    else:
        selected_ids = session[1]

    try:
        char = await get_character(selected_ids[0])
        img, caption = await format_character_info(char)
    except ValueError as e:
        return await message.reply_text(capsify(f"error: {e}"))

    markup = IKM([
        [
            IKB(capsify("⬅️"), callback_data=f"page_{user_id}_3"),
            IKB(capsify("Buy 🔖"), callback_data=f"buy_{user_id}_0"),
            IKB(capsify("➡️"), callback_data=f"page_{user_id}_2")
        ],
        [IKB(capsify("Close 🗑️"), callback_data=f"clos_{user_id}")]
    ])

    await message.reply_photo(img, caption=capsify(f"**Page 1/3**\n\n{caption}"), reply_markup=markup)


@app.on_callback_query(filters.regex(r"^page_"))
@block_cbq
async def page_handler(_, query):
    # FIX: maxsplit=2 taaki char_id mein _ ho toh bhi sahi split ho
    parts = query.data.split("_", 2)
    _, user_id, page = parts
    if int(user_id) != query.from_user.id:
        return await query.answer(capsify("this is not for you, baka!"), show_alert=True)

    user_id, page = int(user_id), int(page)
    session = await get_user_session(user_id)
    if not session or session[0] != today():
        return await query.answer(capsify("session expired! use /store to refresh."), show_alert=True)

    prev_page = 3 if page == 1 else page - 1
    next_page = 1 if page == 3 else page + 1

    char_id = session[1][page - 1]
    try:
        char = await get_character(char_id)
        img, caption = await format_character_info(char)
    except ValueError as e:
        return await query.answer(capsify(f"error: {e}"), show_alert=True)

    markup = IKM([
        [
            IKB(capsify("⬅️"), callback_data=f"page_{user_id}_{prev_page}"),
            IKB(capsify("Buy 🔖"), callback_data=f"buy_{user_id}_{page - 1}"),
            IKB(capsify("➡️"), callback_data=f"page_{user_id}_{next_page}")
        ],
        [IKB(capsify("Close 🗑️"), callback_data=f"clos_{user_id}")]
    ])
    await query.edit_message_media(IMP(img, caption=capsify(f"**Page {page}/3**\n\n{caption}")), reply_markup=markup)


@app.on_callback_query(filters.regex(r"^buy_"))
@block_cbq
async def buy_handler(_, query):
    # FIX: maxsplit=2
    parts = query.data.split("_", 2)
    _, user_id, char_index = parts
    if int(user_id) != query.from_user.id:
        return await query.answer(capsify("this is not for you, baka!"), show_alert=True)

    user_id, char_index = int(user_id), int(char_index)
    session = await get_user_session(user_id)
    if not session:
        return await query.answer(capsify("session expired! use /store to refresh."), show_alert=True)
    char_id = session[1][char_index]

    try:
        char = await get_character(char_id)
    except ValueError as e:
        return await query.answer(capsify(f"error: {e}"), show_alert=True)

    user_balance = await show(user_id)
    # FIX: None check
    if user_balance is None or user_balance < char["price"]:
        return await query.answer(capsify("you don't have enough Exlix!"), show_alert=True)

    markup = IKM([
        [IKB(capsify("Confirm Purchase 💵"), callback_data=f"con_{user_id}_{char_id}")],
        [IKB(capsify("Back 🔙"), callback_data=f"page_{user_id}_{char_index + 1}")]
    ])

    await query.edit_message_caption(
        capsify(f"**Confirm Purchase**\n\n{char['name']} - {char['price']} Exlix"),
        reply_markup=markup
    )


@app.on_callback_query(filters.regex(r"^con_"))
@block_cbq
async def confirm_handler(_, query):

    parts = query.data.split("_", 2)
    if len(parts) != 3:
        return await query.answer(capsify("invalid data."), show_alert=True)
    _, user_id, char_id = parts

    if int(user_id) != query.from_user.id:
        return await query.answer(capsify("this is not for you, baka!"), show_alert=True)

    user_id = int(user_id)

    try:
        char = await get_character(char_id)
    except ValueError as e:
        return await query.answer(capsify(f"error: {e}"), show_alert=True)

    user_balance = await show(user_id)

    if user_balance is None or user_balance < char["price"]:
        return await query.answer(capsify("you don't have enough Exlix!"), show_alert=True)

    bought = await get_user_bought(user_id)
    if bought and bought[0] == today() and char_id in bought[1]:
        return await query.answer(capsify("you already bought this character!"), show_alert=True)

    await deduct(user_id, char["price"])
    updated_bought = [today(), (bought[1] + [char_id]) if bought else [char_id]]
    await update_user_bought(user_id, updated_bought)

    user_collection_entry = await user_collection.find_one({"id": user_id})
    if user_collection_entry:
        await user_collection.update_one(
            {"id": user_id},
            {"$addToSet": {"characters": char}}
        )
    else:
        await user_collection.insert_one(
            {"id": user_id, "characters": [char]}
        )

    markup = IKM([
        [IKB(capsify("Back 🔙"), callback_data=f"page_{user_id}_1")]
    ])

    await query.edit_message_caption(
        capsify(f"**Purchase Successful!**\n\nCharacter **{char['name']}** has been added to your collection."),
        reply_markup=markup
    )
    await query.answer(capsify("purchase successful!"), show_alert=True)


@app.on_callback_query(filters.regex(r"^clos_"))
@block_cbq
async def close_handler(_, query):

    parts = query.data.split("_", 1)
    _, user_id = parts
    if int(user_id) == query.from_user.id:
        await query.message.delete()
    else:
        await query.answer(capsify("this is not for you, baka!"), show_alert=True)
    
