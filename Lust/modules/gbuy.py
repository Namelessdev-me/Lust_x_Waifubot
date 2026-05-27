import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, CallbackQuery
from datetime import datetime, time, timedelta
import pytz
from . import user_collection, app, collection, capsify, show, deduct
from .block import block_dec, block_cbq

ags = {}


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

def is_allowed_time():
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    if now.weekday() != 6:
        return False
    allowed_start = tz.localize(datetime.combine(now.date(), time(5, 30)))
    allowed_end = tz.localize(datetime.combine(now.date(), time(1, 30))) + timedelta(days=1)
    return allowed_start <= now <= allowed_end

def get_rarity_price_multiplier(rarity_number):
    """Get price multiplier based on rarity number"""
    multipliers = {
        1: 1.0,    # Common
        2: 1.5,    # Medium
        3: 2.5,    # Rare
        4: 4.0,    # Legendary
        5: 6.0,    # Nude
        6: 8.0,    # Limited
        7: 12.0,   # Exotic
        8: 20.0,   # Devine
        9: 10.0,   # Wet
    }
    return multipliers.get(rarity_number, 1.0)

def get_rarity_name(rarity_number):
    """Get rarity name from rarity number"""
    return rarity_map.get(rarity_number, "⚪ Common")

@app.on_message(filters.command("gbuy"))
@block_dec
async def gbuy(client, message):
    if not is_allowed_time():
        await message.reply_text(capsify("This command can only be used on Sundays between 5:30 AM and 1:30 AM."))
        return

    user_id = message.from_user.id
    args = message.command[1:]
    if not args:
        await message.reply_text(capsify("Please provide a character ID to buy. Usage: /gbuy <character_id>"))
        return

    character_id = args[0]
    character = await collection.find_one({'id': character_id})

    if not character:
        await message.reply_text(capsify("Character not found. Please provide a valid character ID."))
        return


    rarity_value = character.get('rarity')
    

    restricted_rarities = [7, 8, 9]  # Exotic, Devine, Wet cannot be gbuy'd
    if isinstance(rarity_value, int) and rarity_value in restricted_rarities:
        await message.reply_text(capsify("❌ This character cannot be purchased with /gbuy command."))
        return
    

    if isinstance(rarity_value, int):
        rarity_name = get_rarity_name(rarity_value)
        multiplier = get_rarity_price_multiplier(rarity_value)
    else:

        rarity_name = str(rarity_value)
        multiplier = 1.0


    base_price = 60000
    price = int(base_price * multiplier)
    

    price = random.randint(int(price * 0.9), int(price * 1.1))

    
    user_balance = await show(user_id)
    
    keyboard = [
        [IKB(capsify("Buy"), callback_data=f"gbuy_confirm:{character_id}:{price}:{user_id}"),
         IKB(capsify("Cancel"), callback_data=f"gbuy_cancel:{character_id}:{user_id}")]
    ]
    reply_markup = IKM(keyboard)

    caption = capsify(
        f"**🎯 Character Purchase**\n\n"
        f"**Name:** {character['name']}\n"
        f"**ID:** {character['id']}\n"
        f"**Rarity:** {rarity_name}\n"
        f"**Price:** {price:,} Exlix\n"
        f"**Your Balance:** {user_balance:,} Exlix\n\n"
        f"Do you want to purchase this character?"
    )

    msg = await message.reply_photo(
        photo=character['img_url'],
        caption=caption,
        reply_markup=reply_markup
    )

    ags[msg.message_id] = user_id

@app.on_callback_query(filters.regex(r"^(gbuy_confirm|gbuy_cancel):"))
async def handle_gbuy_callback(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data.split(":")
    action = data[0]
    character_id = data[1]
    
    if action == "gbuy_confirm":
        price = int(data[2])
        callback_user_id = int(data[3])
        
        if user_id != callback_user_id:
            await query.answer(capsify("This action is not for you."))
            return

        user_balance = await show(user_id)
        if user_balance < price:
            await query.answer(capsify("❌ You don't have enough Exlix!"))
            return
        
        character = await collection.find_one({'id': character_id})
        if not character:
            await query.answer(capsify("Character not found."))
            return
        
        
        user_data = await user_collection.find_one({'id': user_id})
        if user_data and 'characters' in user_data:
            existing_ids = [char.get('id') for char in user_data['characters']]
            if character_id in existing_ids:
                await query.answer(capsify("❌ You already own this character!"))
                return
        

        await deduct(user_id, price)
        

        if user_data:
            await user_collection.update_one(
                {'id': user_id}, 
                {'$push': {'characters': character}}
            )
        else:
            await user_collection.insert_one({
                'id': user_id, 
                'characters': [character],
                'gold': 0,
                'exlix': 0
            })
        

        await query.message.edit_caption(
            caption=capsify(f"✅ Purchase successful!\n\nYou bought **{character['name']}** for **{price:,} Exlix**."),
            reply_markup=None
        )
        

        if query.message.message_id in ags:
            del ags[query.message.message_id]
        
        await query.answer("✅ Purchase completed!")
        
    elif action == "gbuy_cancel":
        callback_user_id = int(data[2])
        
        if user_id != callback_user_id:
            await query.answer(capsify("This action is not for you."))
            return
        
        await query.message.edit_caption(
            caption=capsify("❌ Purchase cancelled."),
            reply_markup=None
        )
        

        if query.message.message_id in ags:
            del ags[query.message.message_id]
        
        await query.answer("❌ Purchase cancelled.")
