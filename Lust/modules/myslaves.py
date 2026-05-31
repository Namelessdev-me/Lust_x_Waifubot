import asyncio
import math
from itertools import groupby
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from . import user_collection, capsify, app
from .block import temp_block, block_cbq

AUTO_DELETE_SECONDS = 200

async def auto_delete(msg, delay=AUTO_DELETE_SECONDS):
    """Delete a message after `delay` seconds."""
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


async def build_myslaves(user_id, page=0):
    user = await user_collection.find_one({'id': user_id})
    if not user:
        return None, None, None

    cmode = user.get('collection_mode', 'All')
    characters = [c for c in user.get('characters', []) if cmode == 'All' or c.get('rarity', '') == cmode]
    characters = sorted(characters, key=lambda x: (x.get('anime', ''), x.get('id', '')))

    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}
    unique_characters = list({c['id']: c for c in characters}.values())

    total_pages = max(1, math.ceil(len(unique_characters) / 10))
    if page < 0 or page >= total_pages:
        page = 0

    username = user.get('first_name', 'User')

    current_characters = unique_characters[page * 10:(page + 1) * 10]
    grouped = {}
    for c in current_characters:
        anime = c.get('anime', 'Unknown')
        if anime not in grouped:
            grouped[anime] = []
        grouped[anime].append(c)

    anime_totals = {}
    for c in unique_characters:
        anime = c.get('anime', 'Unknown')
        anime_totals[anime] = anime_totals.get(anime, 0) + 1

    myslaves_message = f"𓆩 {capsify(username)}'s Harem\n"
    myslaves_message += capsify(f"Total Waifus: {len(unique_characters)}\n")
    myslaves_message += capsify(f"Page {page+1}/{total_pages}\n")

    for anime, chars in grouped.items():
        anime_count_on_page = len(chars)
        anime_total = anime_totals.get(anime, 0)
        myslaves_message += f"\n⌬ {anime} 〔{anime_count_on_page}/{anime_total}〕\n"
        for character in chars:
            count = character_counts.get(character['id'], 1)
            rarity = character.get('rarity', '')
            char_id = character['id']
            name = character['name']
            myslaves_message += f"➥ {rarity} {char_id} {capsify(name)} ×{count}\n"

    inline_query = f"collection.{user_id}"
    if cmode != 'All':
        inline_query += f".{cmode}"


    keyboard = [
        [
            IKB("👁 ᴠɪᴇᴡ", switch_inline_query_current_chat=inline_query),
            IKB("🍹 ꜱʟᴀᴠᴇ", switch_inline_query_current_chat=f"collection.{user_id}"),
            IKB("🎥 ᴀɴɪ", switch_inline_query_current_chat=f"vcollection.{user_id}")
        ]
    ]

    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(IKB("◄", callback_data=f"myslaves:{page-1}:{user_id}"))
        if page < total_pages - 1:
            nav_buttons.append(IKB("►", callback_data=f"myslaves:{page+1}:{user_id}"))
        if nav_buttons:
            keyboard.append(nav_buttons)

        skip_buttons = []
        if page > 4:
            skip_buttons.append(IKB("«5", callback_data=f"myslaves:{page-5}:{user_id}"))
        if page < total_pages - 5:
            skip_buttons.append(IKB("5»", callback_data=f"myslaves:{page+5}:{user_id}"))
        if skip_buttons:
            keyboard.append(skip_buttons)

    keyboard.append([IKB("✖", callback_data=f"myslaves:close_{user_id}")])
    markup = IKM(keyboard)

    fav_media = None
    fav_type = "photo"
    if user.get('favorites'):
        fav_id = user['favorites'][0]
        fav_char = next((c for c in user.get('characters', []) if c['id'] == fav_id), None)
        if fav_char and 'img_url' in fav_char:
            fav_media = fav_char['img_url']
            fav_type = fav_char.get('type', 'photo')

    return myslaves_message, markup, (fav_media, fav_type)


@app.on_message(filters.command(["myslaves", "collection"]))
async def myslaves_cmd(client, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    text, markup, media_info = await build_myslaves(user_id, 0)
    if not text:
        sent = await message.reply_text(capsify("You have not grabbed any slaves yet..."))
        asyncio.create_task(auto_delete(sent))
        return

    fav_media, fav_type = media_info
    if fav_media:
        try:
            if fav_type == "video":
                sent = await app.send_video(message.chat.id, video=fav_media, caption=text, reply_markup=markup, reply_to_message_id=message.id)
            else:
                sent = await app.send_photo(message.chat.id, photo=fav_media, caption=text, reply_markup=markup, reply_to_message_id=message.id)
            asyncio.create_task(auto_delete(sent))
            return
        except Exception:
            pass

    sent = await message.reply_text(text, reply_markup=markup)
    asyncio.create_task(auto_delete(sent))


@app.on_callback_query(filters.regex(r"^myslaves:"))
@block_cbq
async def myslaves_callback(client, callback_query):
    data = callback_query.data

    if "close_" in data:
        end_user = int(data.split("close_")[1])
        if end_user == callback_query.from_user.id:
            await callback_query.answer()
            await callback_query.message.delete()
        else:
            await callback_query.answer(capsify("This is not your Myslaves"), show_alert=True)
        return

    parts = data.split(":")
    if len(parts) != 3:
        await callback_query.answer("Invalid data", show_alert=True)
        return

    _, page_str, user_id_str = parts
    page = int(page_str)
    user_id = int(user_id_str)

    if callback_query.from_user.id != user_id:
        await callback_query.answer(capsify("This is not your Myslaves"), show_alert=True)
        return

    text, markup, media_info = await build_myslaves(user_id, page)
    if not text:
        await callback_query.answer(capsify("No data found"), show_alert=True)
        return

    await callback_query.answer()
    try:
        await callback_query.message.edit_text(text, reply_markup=markup)
    except Exception:
        await callback_query.message.edit_caption(caption=text, reply_markup=markup)
