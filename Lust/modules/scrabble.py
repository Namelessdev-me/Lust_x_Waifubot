import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import random
from datetime import datetime
from pytz import timezone
from . import collection, user_collection, app, capsify, nopvt, add
from .watchers import scrabble_watcher
from .block import block_dec, temp_block

AUTO_DELETE_SECONDS = 120

async def auto_delete(msg, delay=AUTO_DELETE_SECONDS):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass

active_scrabbles = {}
MAX_ATTEMPTS = 5
WIN_LIMIT = 3
COOLDOWN_TIME = 30
cooldown_users = {}

SCRABBLE_RARITY_ENABLED = {
    "⚪ Common":    True,
    "☘️ Medium":   True,
    "🔴 Rare":     True,
    "🟡 Legendary": True,
    "💋 Nude":      False,
    "🔮 Limited":   True,
    "🐦‍🔥 Exotic":  False,
    "🎐 Devine":    False,
    "💦 Wet":       False,
    "🎥 Animation": False
}

def is_new_day(last_win_time):
    ist = timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    last_win_ist = last_win_time.astimezone(ist)
    return now_ist.date() != last_win_ist.date()

async def get_random_character():
    all_characters = await collection.find({
        'id': {'$gte': '01', '$lte': '1100'}
    }).to_list(length=None)

    enabled_characters = [
        c for c in all_characters
        if SCRABBLE_RARITY_ENABLED.get(c.get('rarity', ''), True)
    ]

    pool = enabled_characters if enabled_characters else all_characters

    while True:
        character = random.choice(pool)
        if len(character['name'].split()[0]) > 3:
            return character

def scramble_word(word):
    if len(word) <= 3:
        return word
    word_list = list(word)
    random.shuffle(word_list)
    return ''.join(word_list)

def provide_hint(word, attempts):
    if attempts == 1:
        return f"{word[:2]}{'_' * (len(word) - 2)}"
    elif attempts == 2:
        return f"{word[:2]}{'_' * (len(word) - 3)}{word[-1]}"
    else:
        return f"{word[:2]}{'_' * (len(word) - 3)}{word[-1]}"

@app.on_message(filters.command("scrabble"))
@block_dec
@nopvt
async def scrabble(client, message: Message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    chat_id = message.chat.id

    if user_id in cooldown_users:
        remaining_time = COOLDOWN_TIME - (datetime.now() - cooldown_users[user_id]).total_seconds()
        remaining_time = max(remaining_time, 0)
        sent = await message.reply_text(capsify(f"Please wait {int(remaining_time)} seconds before starting a new game."))
        asyncio.create_task(auto_delete(sent))
        return

    if user_id in active_scrabbles:
        sent = await message.reply_text(capsify("You already have an active scrabble. Please wait for it to finish."))
        asyncio.create_task(auto_delete(sent))
        return

    character = await get_random_character()
    first_word = character['name'].split()[0]
    scrambled_word = scramble_word(first_word)

    active_scrabbles[user_id] = {
        'character': character,
        'word': first_word,
        'scrambled_word': scrambled_word,
        'start_time': datetime.now(),
        'attempts': 0
    }

    sent = await message.reply_text(
        f"{capsify('Welcome to Word Scramble!')}\n\n"
        f"Can you unscramble this word? Try it out:\n\n"
        f"{scrambled_word}\n\n"
        f"⏳ You have {MAX_ATTEMPTS} attempts to respond.\n"
        f"⏳ Use /xscrabble to terminate the game."
    )
    asyncio.create_task(auto_delete(sent))

@app.on_message(~filters.me, group=scrabble_watcher)
async def check_answer(client, message: Message):
    if message.from_user is None:
        return

    user_id = message.from_user.id

    if user_id not in active_scrabbles:
        return

    if message.sticker:
        return

    if message.text.startswith('/'):
        return

    answer = message.text.strip()
    scrabble_data = active_scrabbles[user_id]
    scrabble_data['attempts'] += 1

    user_data = await user_collection.find_one({'id': user_id})

    if not user_data:
        user_data = {'id': user_id, 'wins': 0, 'last_win_time': datetime.min}
    else:
        if 'wins' not in user_data:
            user_data['wins'] = 0

    if answer.lower() == scrabble_data['word'].lower():
        now = datetime.now()

        user_data['wins'] += 1
        user_data['last_win_time'] = now

        await user_collection.replace_one({'id': user_id}, user_data, upsert=True)

        if user_data['wins'] <= WIN_LIMIT:
            try:
                sent = await message.reply_photo(
                    photo=scrabble_data['character']['img_url'],
                    caption=capsify(f"{scrabble_data['character']['name']} added to your collection! 🎉")
                )
                asyncio.create_task(auto_delete(sent))
            except Exception:
                sent = await message.reply_text(capsify(f"{scrabble_data['character']['name']} added to your collection! 🎉"))
                asyncio.create_task(auto_delete(sent))

            await user_collection.update_one({'id': user_id}, {'$push': {'characters': scrabble_data['character']}})
            if user_data['wins'] == WIN_LIMIT:
                sent = await message.reply_text(capsify("🎉 You won 3 games today! Now you will get Exlix instead of characters. 🪙"))
                asyncio.create_task(auto_delete(sent))
        else:
            exlix = random.randint(15000, 20000)
            sent = await message.reply_text(capsify(f"💰 You've won {exlix} Exlix! 💰"))
            asyncio.create_task(auto_delete(sent))
            await add(user_id, exlix)

        del active_scrabbles[user_id]

        cooldown_users[user_id] = datetime.now()
        asyncio.create_task(remove_cooldown(user_id))

    elif scrabble_data['attempts'] >= MAX_ATTEMPTS:
        sent = await message.reply_text(
            capsify(f"❌ Out of attempts! ❌\nCorrect answer was: {scrabble_data['word']}")
        )
        asyncio.create_task(auto_delete(sent))
        del active_scrabbles[user_id]
    else:
        hint = provide_hint(scrabble_data['word'], scrabble_data['attempts'])
        sent = await message.reply_text(
            capsify(f"❌ Incorrect Answer! ❌\n\n"
            f"Scrambled word: {scrabble_data['scrambled_word']}\n\n"
            f"Hint: {hint}\n\n"
            f"Try again! 🔄")
        )
        asyncio.create_task(auto_delete(sent))

async def remove_cooldown(user_id):
    await asyncio.sleep(COOLDOWN_TIME)
    if user_id in cooldown_users:
        del cooldown_users[user_id]

@app.on_message(filters.command("xscrabble"))
async def xscrabble(client, message: Message):
    user_id = message.from_user.id

    if user_id in active_scrabbles:
        del active_scrabbles[user_id]
        sent = await message.reply_text(capsify("Your current game has been terminated."))
        asyncio.create_task(auto_delete(sent))
    else:
        sent = await message.reply_text(capsify("You don't have an active game to terminate."))
        asyncio.create_task(auto_delete(sent))
