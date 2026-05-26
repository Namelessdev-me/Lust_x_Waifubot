from pyrogram import filters
from Lust import application, user_collection
from . import app as bot
from pyrogram.types import Message
from html import escape
from telegram.ext import CommandHandler
from .block import block_dec
XP_PER_LEVEL = 40

LEVEL_TITLES = {
    (0, 10): "👤 Rokki",
    (11, 30): "🌟 F",
    (31, 50): "⚡️ E",
    (51, 75): "🔫 D",
    (76, 100): "🛡 C",
    (101, 125): "🗡 B",
    (126, 150): "⚔️ A",
    (151, 175): "🎖 S",
    (176, 200): "🔱 National",
    (201, 2000): "👑 Monarch",
}

def calculate_level(xp):
    return xp // XP_PER_LEVEL

def get_user_level_title(user_level):
    for level_range, title in LEVEL_TITLES.items():
        if level_range[0] <= user_level <= level_range[1]:
            return title
    return "👤 Rokki"

@bot.on_message(filters.command(["xp"]))
@block_dec
async def check_stats(_, message: Message):
    user_id = message.from_user.id
    replied_user_id = None
    
    if message.reply_to_message:
        replied_user_id = message.reply_to_message.from_user.id
    
    if replied_user_id:
        user_id = replied_user_id
    
    user_data = await user_collection.find_one({'id': user_id})
    
    if not user_data:
        return await message.reply_text("You need to start the bot first.")
    
    user_xp_data = await user_collection.find_one({'id': user_id})
    
    if user_xp_data:
        user_xp = user_xp_data.get('xp', 0)
        user_level = user_xp // XP_PER_LEVEL
        user_level_title = get_user_level_title(user_level)
        first_name = user_data.get('first_name', 'User')
        await message.reply_text(f"{first_name} is a {user_level_title} rank at level {user_level} with {user_xp} XP.")
    else:
        await message.reply_text("You don't have any XP yet.")

async def xtop(update, context):
    top_users = await user_collection.find({}, projection={'id': 1, 'first_name': 1, 'last_name': 1, 'xp': 1}).sort('xp', -1).limit(10).to_list(10)
    top_users_message = "Top 10 XP Users:\n───────────────────\n"
    
    for i, user in enumerate(top_users, start=1):
        first_name = user.get('first_name', 'Unknown')
        last_name = user.get('last_name', '')
        user_id = user.get('id', 'Unknown')
        full_name = f"{first_name} {last_name}" if last_name else first_name
        user_link = f"<a href='tg://user?id={user_id}'>{escape(first_name)}</a>"
        top_users_message += f"{i}. {user_link} - ({user.get('xp', 0):,.0f} xp)\n"
    
    top_users_message += "────────────────────\nTop 10 Users via @Guess_Yourr_Slave_bot"
    photo_path = 'https://telegra.ph/file/0dd6484b96c63f06379ef.jpg'
    await update.message.reply_photo(photo=photo_path, caption=top_users_message, parse_mode='HTML')

application.add_handler(CommandHandler("xtop", xtop, block=False))