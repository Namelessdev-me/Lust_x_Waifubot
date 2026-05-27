from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from . import user_collection, app
from .block import block_dec, temp_block, block_cbq

FONT_PATH = "Fonts/font.ttf"
CATBOX_VIDEO_URL = "https://files.catbox.moe/xh7kv5.mp4"

rarity_map = {
    1: "⚪ Common",
    2: "☘️ Medium",
    3: "🔴 Rare",
    4: "🟡 Legendary",
    5: "💋 Nude",
    6: "🔮 Limited",
    7: "🐦‍🔥 Exotic",
    8: "🎐 Devine",
    9: "💦 Wet",
    10: "🎥 Animation"
}

rarity_name_to_code = {
    "common": 1,
    "medium": 2,
    "rare": 3,
    "legendary": 4,
    "nude": 5,
    "limited": 6,
    "exotic": 7,
    "devine": 8,
    "wet": 9,
    "animation": 10,
    "all": "all"
}

@app.on_message(filters.command("cmode") & filters.group)
async def cmode(client, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    username = message.from_user.username or "None"

    user_data = await user_collection.find_one({'id': user_id})
    current_rarity = user_data.get('collection_mode', 'All') if user_data else 'All'

    cmode_buttons = [
        [IKB("⚪ Common", f"cmode:common:{user_id}"), IKB("☘️ Medium", f"cmode:medium:{user_id}")],
        [IKB("🔴 Rare", f"cmode:rare:{user_id}"), IKB("🟡 Legendary", f"cmode:legendary:{user_id}")],
        [IKB("💋 Nude", f"cmode:nude:{user_id}"), IKB("🔮 Limited", f"cmode:limited:{user_id}")],
        [IKB("🐦‍🔥 Exotic", f"cmode:exotic:{user_id}"), IKB("🎐 Devine", f"cmode:devine:{user_id}")],
        [IKB("💦 Wet", f"cmode:wet:{user_id}"), IKB("🎥 Animation", f"cmode:animation:{user_id}")],
        [IKB("All", f"cmode:all:{user_id}")]
    ]
    reply_markup = IKM(cmode_buttons)

    response_text = f"Username: {username}\n"
    response_text += f"User ID: {user_id}\n"
    response_text += f"Current Mode: {current_rarity}\n\n"
    response_text += "Choose your collection mode:"

    await message.reply_video(
        video=CATBOX_VIDEO_URL,
        caption=response_text,
        reply_markup=reply_markup
    )

@app.on_callback_query(filters.regex(r"^cmode:"))
async def cmode_callback(client, callback_query):
    data = callback_query.data
    _, rarity_key, user_id = data.split(':')
    user_id = int(user_id)
    
    if callback_query.from_user.id != user_id:
        await callback_query.answer("You cannot change someone else's collection mode.", show_alert=True)
        return

    user_data = await user_collection.find_one({'id': user_id})
    if not user_data:
        await callback_query.answer("User data not found.", show_alert=True)
        return

    if rarity_key == "all":
        collection_mode = "All"
    else:
        rarity_code = rarity_name_to_code.get(rarity_key)
        if not rarity_code:
            await callback_query.answer("Invalid rarity selected.", show_alert=True)
            return
        collection_mode = rarity_map.get(rarity_code, "Unknown")

    if rarity_key != "all":
        characters = [char for char in user_data.get('characters', []) 
                     if char.get('rarity_code') == rarity_code or 
                        char.get('rarity') == collection_mode]
        
        if not characters:
            await callback_query.answer(
                f"You don't have any characters with the rarity: {collection_mode}.", 
                show_alert=True
            )
            return

    await user_collection.update_one(
        {'id': user_id}, 
        {'$set': {'collection_mode': collection_mode}}
    )

    username = callback_query.from_user.username or "None"
    
    response_text = f"Username: {username}\n"
    response_text += f"User ID: {user_id}\n"
    response_text += f"Mode Set To: {collection_mode}\n\n"
    response_text += f"✓ Collection mode successfully updated!"

    await callback_query.edit_message_caption(
        caption=response_text
    )

@app.on_message(filters.command("cmode") & filters.private)
async def cmode_private(client, message):
    await message.reply_text("This command only works in groups.")
