import re
import time
from cachetools import TTLCache
from pymongo import DESCENDING
import asyncio

from telegram import Update
from telegram.ext import InlineQueryHandler, CallbackContext
from telegram import (
InlineKeyboardButton as IKB,
InlineKeyboardMarkup as IKM,
InlineQueryResultPhoto as IQP,
InlineQueryResultVideo as IQV,
InlineQueryResultCachedPhoto as IQCP,
InlineQueryResultCachedVideo as IQCV
)

from . import user_collection, collection, application, db, capsify
from .block import block_inl_ptb

lock = asyncio.Lock()

db.characters.create_index([('id', DESCENDING)])
db.characters.create_index([('anime', DESCENDING)])
db.characters.create_index([('img_url', DESCENDING)])
db.user_collection.create_index([('characters.id', DESCENDING)])

all_characters_cache = TTLCache(maxsize=10000, ttl=36000)

RARITY_MAP = {
    1:  "⚪ Common",
    2:  "☘️ Medium",
    3:  "🔴 Rare",
    4:  "🟡 Legendary",
    5:  "💋 Nude",
    6:  "🔮 Limited",
    7:  "🐦‍🔥 Exotic",
    8:  "🎐 Devine",
    9:  "💦 Wet",
    10: "🎥 Animation"
}

CATEGORY_MAP = {
    '🎒': '🎒 𝑪𝒍𝒂𝒔𝒔𝒓𝒐𝒐𝒎 𝑸𝒖𝒆𝒆𝒏 🎒',
    '💉': '💉 𝑾𝒉𝒊𝒕𝒆 𝑮𝒓𝒂𝒄𝒆 💉',
    '🧹': '🧹 𝑪𝒉𝒂𝒓𝒎 𝑴𝒂𝒊𝒅𝒆𝒏 🧹',
    '🐰': '🐰 𝑴𝒐𝒐𝒏𝒍𝒊𝒕 𝑩𝒐𝒖𝒏𝒄𝒆 🐰',
    '👘': '👘 𝑺𝒂𝒌𝒖𝒓𝒂 𝑮𝒓𝒂𝒄𝒆 👘',
    '💍': '💍 𝑭𝒐𝒓𝒆𝒗𝒆𝒓 𝑩𝒍𝒊𝒔𝒔 💍',
    '🎊': '🎊 𝑽𝒊𝒃𝒆 𝑬𝒏𝒆𝒓𝒈𝒚 🎊',
    '🚓': '🚓 𝑱𝒖𝒔𝒕𝒊𝒄𝒆 𝑬𝒏𝒄𝒉𝒂𝒏𝒕𝒓𝒆𝒔𝒔 🚓',
    '🥻': '🥻 𝑬𝒕𝒉𝒆𝒓𝒆𝒂𝒍 𝑮𝒆𝒎 🥻',
    '🕷': '🕷 𝑵𝒆𝒕 𝑺𝒐𝒓𝒄𝒆𝒓𝒆𝒔𝒔 🕷',
    '🏜': '🏜 𝑺𝒂𝒏𝒅𝒔 𝑬𝒎𝒑𝒓𝒆𝒔𝒔 🏜',
    '⚜️': '⚜️ 𝑺𝒂𝒄𝒓𝒆𝒅 𝑶𝒂𝒕𝒉 ⚜️',
    '🩸': '🩸 𝑵𝒐𝒄𝒕𝒖𝒓𝒏𝒂𝒍 𝑹𝒐𝒔𝒆 🩸',
    '🕊️': '🕊️ 𝑾𝒊𝒏𝒈𝒔 𝒐𝒇 𝑭𝒂𝒕𝒆 🕊️',
    '☃️': '☃️ 𝑺𝒏𝒐𝒘𝒇𝒂𝒍𝒍 𝑬𝒍𝒍𝒆 ☃️',
    '💞': '💞 𝑯𝒆𝒂𝒓𝒕𝒔𝒐𝒏𝒈 𝑫𝒖𝒄𝒉𝒆𝒔𝒔 💞',
    '🏖': '🏖 𝑺𝒖𝒏𝒌𝒊𝒔𝒔 𝑺𝒆𝒓𝒆𝒏𝒂𝒅𝒆 🏖',
    '🎃': '🎃 𝑺𝒑𝒆𝒍𝒍𝒃𝒐𝒖𝒏𝒅 𝑾𝒊𝒕𝒄𝒉 🎃',
    '🎮': '🎮 𝑮𝒂𝒎𝒆 𝑮𝒐𝒅𝒅𝒆𝒔𝒔 🎮'
}


def is_url(val):
    return isinstance(val, str) and val.startswith("http")


def build_result(character, from_user_id):
    """Build inline result — URL → IQP/IQV, file_id → IQCP/IQCV"""
    rarity = RARITY_MAP.get(character.get("rarity"), character.get("rarity", ""))
    cat_key = character.get("category", "")
    category = CATEGORY_MAP.get(cat_key, "")

    caption = (
        "✦ 𝗢𝘄𝗢! 𝗖𝗵𝗲𝗰𝗸 𝗢𝘂𝘁 𝗧𝗵𝗶𝘀 𝗖𝗵𝗮𝗿𝗮𝗰𝗧𝗲𝗿! ✦\n\n"
        f"『 {character['anime']} 』\n"
        f"✧ {character['id']}: {character['name']}\n"
        f"{category}\n"
        f"({rarity})"
    )

    keyboard = [[IKB(
        capsify("How many I have ❓"),
        callback_data=f"check_{from_user_id}_{character['id']}"
    )]]
    reply_markup = IKM(keyboard)

    img = character.get("img_url", "")
    char_type = character.get("type", "photo")
    uid = f"{character['id']}_{int(time.time())}"

    if is_url(img):

        if char_type == "video":
            return IQV(
                id=uid,
                video_url=img,
                mime_type="video/mp4",
                thumbnail_url=img,
                title=character["name"],
                caption=caption,
                reply_markup=reply_markup
            )
        else:
            return IQP(
                id=uid,
                photo_url=img,
                thumbnail_url=img,
                caption=caption,
                reply_markup=reply_markup
            )
    else:

        if char_type == "video":
            return IQCV(
                id=uid,
                video_file_id=img,
                title=character["name"],
                caption=caption,
                reply_markup=reply_markup
            )
        else:
            return IQCP(
                id=uid,
                photo_file_id=img,
                caption=caption,
                reply_markup=reply_markup
            )


@block_inl_ptb
async def inlinequery(update: Update, context: CallbackContext):
    query = update.inline_query.query.strip()
    from_user_id = update.inline_query.from_user.id

    
    if query.startswith("collection.") or query.startswith("vcollection."):
        parts = query.split(".")
        user_id = int(parts[1])
        video_only = query.startswith("vcollection.")

        user = await user_collection.find_one({'id': user_id})
        if not user:
            await update.inline_query.answer([], cache_time=1)
            return

        user_chars = user.get("characters", [])
        if not user_chars:
            await update.inline_query.answer([], cache_time=1)
            return


        char_ids = list({c["id"] for c in user_chars if "id" in c})
        db_chars = await collection.find(
            {"id": {"$in": char_ids}},
            {'name': 1, 'anime': 1, 'img_url': 1, 'id': 1, 'rarity': 1, 'type': 1, 'category': 1}
        ).to_list(length=None)
        char_map = {c["id"]: c for c in db_chars}

        results = []
        seen_ids = set()
        for char in user_chars:
            cid = char.get("id")
            if not cid or cid in seen_ids:
                continue
            character = char_map.get(cid)
            if not character:
                continue
            if video_only and character.get("type") != "video":
                continue
            seen_ids.add(cid)
            results.append(build_result(character, from_user_id))

        try:
            await update.inline_query.answer(results[:1000], cache_time=5)
        except Exception:
            pass
        return

    
    offset = int(update.inline_query.offset) if update.inline_query.offset else 0
    results_per_page = 15
    start_index = offset
    end_index = offset + results_per_page

    if not query:
        if 'all_characters' in all_characters_cache:
            all_characters = all_characters_cache['all_characters']
        else:
            all_characters = await collection.find({}, {
                'name': 1, 'anime': 1, 'img_url': 1, 'id': 1, 'rarity': 1, 'type': 1, 'category': 1
            }).to_list(length=None)
            all_characters_cache['all_characters'] = all_characters
    else:
        regex = re.compile(query, re.IGNORECASE)
        all_characters = await collection.find(
            {"$or": [{"name": regex}, {"anime": regex}]},
            {'name': 1, 'anime': 1, 'img_url': 1, 'id': 1, 'rarity': 1, 'type': 1, 'category': 1}
        ).to_list(length=None)

    characters = list(all_characters)[start_index:end_index]
    results = [build_result(c, from_user_id) for c in characters]

    next_offset = str(end_index) if len(characters) == results_per_page else ""

    try:
        await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)
    except Exception:
        pass


application.add_handler(InlineQueryHandler(inlinequery, block=False))
