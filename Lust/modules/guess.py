import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import random
from datetime import datetime
from pytz import timezone
from . import add, capsify, sudo_filter, guess_watcher, nopvt, app, collection, limit, user_collection
from .block import block_dec

AUTO_DELETE_SECONDS = 120
COOLDOWN_TIME = 30
GUESS_TIMEOUT = 60

# Rarities that should never spawn in the guessing game
EXCLUDED_RARITIES = {"animation", "animated"}

active_guesses = {}   # chat_id -> game_data
cooldown_users = {}   # user_id -> datetime
streaks = {}          # user_id -> int (current streak count)


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────

async def auto_delete(msg, delay=AUTO_DELETE_SECONDS):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


async def get_random_character():
    """Return a random character, excluding animation-rarity ones."""
    all_characters = await collection.find({}).to_list(length=None)
    filtered = [
        c for c in all_characters
        if str(c.get("rarity", "")).lower() not in EXCLUDED_RARITIES
    ]
    if not filtered:
        # Fallback: use full list if somehow everything is filtered out
        filtered = all_characters
    return random.choice(filtered)


async def remove_cooldown(user_id):
    await asyncio.sleep(COOLDOWN_TIME)
    cooldown_users.pop(user_id, None)


async def spawn_next(client, chat_id, reply_target):
    """Spawn the next character in an ongoing auto-chain."""
    character = await get_random_character()

    active_guesses[chat_id] = {
        'character': character,
        'start_time': datetime.now(),
        'guessed': False,
        'message_id': reply_target.id,
    }

    sent = await reply_target.reply_photo(
        photo=character['img_url'],
        caption=capsify("🔁 Next character! Guess the name to win Exlix!")
    )
    asyncio.create_task(auto_delete(sent))
    asyncio.create_task(check_timeout(client, reply_target, chat_id))


# ──────────────────────────────────────────────
#  /guess  – start a new game
# ──────────────────────────────────────────────

@app.on_message(filters.command("guess"))
@block_dec
async def guess(client, message: Message):
    chat_id = message.chat.id

    if chat_id in active_guesses:
        sent = await message.reply_text(
            capsify("A guessing game is already running in this chat!")
        )
        asyncio.create_task(auto_delete(sent))
        return

    character = await get_random_character()

    active_guesses[chat_id] = {
        'character': character,
        'start_time': datetime.now(),
        'guessed': False,
        'message_id': message.id,
    }

    sent = await message.reply_photo(
        photo=character['img_url'],
        caption=capsify("🎮 Guess the character's name! First correct guess wins 8000–12000 Exlix!")
    )
    asyncio.create_task(auto_delete(sent))
    asyncio.create_task(check_timeout(client, message, chat_id))


# ──────────────────────────────────────────────
#  Guess watcher – handles incoming answers
# ──────────────────────────────────────────────

@app.on_message(~filters.me, group=guess_watcher)
async def check_guess(client, message: Message):
    chat_id = message.chat.id

    if not message.from_user or chat_id not in active_guesses:
        return

    game_data = active_guesses[chat_id]

    if game_data['guessed'] or not message.text:
        return

    user_id = message.from_user.id

    # Cooldown check
    if user_id in cooldown_users:
        remaining = COOLDOWN_TIME - (datetime.now() - cooldown_users[user_id]).total_seconds()
        if remaining > 0:
            return

    answer = message.text.strip().lower()
    correct_name = game_data['character']['name'].lower()
    name_parts = correct_name.split()

    if not any(part in answer for part in name_parts):
        return

    # ── Correct guess ──
    game_data['guessed'] = True
    reward = random.randint(8000, 12000)
    await add(user_id, reward)

    # Update streak
    streaks[user_id] = streaks.get(user_id, 0) + 1
    current_streak = streaks[user_id]
    streak_text = f" 🔥 Streak: {current_streak}" if current_streak > 1 else ""

    sent = await message.reply_text(
        capsify(
            f"🎉 Correct, {message.from_user.first_name}! "
            f"You won {reward} Exlix!{streak_text}"
        )
    )
    asyncio.create_task(auto_delete(sent))

    # Apply cooldown
    cooldown_users[user_id] = datetime.now()
    asyncio.create_task(remove_cooldown(user_id))

    # Remove current game then auto-spawn next character
    del active_guesses[chat_id]
    asyncio.create_task(spawn_next(client, chat_id, message))


# ──────────────────────────────────────────────
#  Timeout – stops the chain if nobody guesses
# ──────────────────────────────────────────────

async def check_timeout(client, message: Message, chat_id):
    await asyncio.sleep(GUESS_TIMEOUT)

    if chat_id not in active_guesses:
        return  # Already guessed; spawn_next took over

    game_data = active_guesses[chat_id]
    if game_data['guessed']:
        return

    # Nobody guessed — reveal answer, reset ALL streaks for this chat, and stop
    character = game_data['character']
    original_message_id = game_data['message_id']

    # Reset streaks for everyone who was on a streak (optional: only active users)
    # Here we simply leave individual streaks intact but you can clear them if desired.
    # To reset ALL streaks globally on timeout, uncomment:
    # streaks.clear()

    sent = await message.reply_text(
        capsify(
            f"⌛ Time's up! Nobody guessed it.\n"
            f"The answer was: {character['name']}\n"
            f"Game stopped — use /guess to start again."
        ),
        reply_to_message_id=original_message_id
    )
    asyncio.create_task(auto_delete(sent))
    del active_guesses[chat_id]


# ──────────────────────────────────────────────
#  /xguess  – sudo force-stop
# ──────────────────────────────────────────────

@app.on_message(filters.command("xguess") & sudo_filter)
@block_dec
async def xguess(client, message: Message):
    chat_id = message.chat.id

    if chat_id in active_guesses:
        del active_guesses[chat_id]
        sent = await message.reply_text(
            capsify("The current guessing game has been terminated.")
        )
    else:
        sent = await message.reply_text(
            capsify("There is no active guessing game to terminate.")
        )
    asyncio.create_task(auto_delete(sent))


# ──────────────────────────────────────────────
#  /streak  – check your current streak
# ──────────────────────────────────────────────

@app.on_message(filters.command("streak"))
@block_dec
async def streak_cmd(client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return

    current = streaks.get(user_id, 0)
    if current == 0:
        text = "You don't have an active streak yet. Start guessing!"
    else:
        text = f"🔥 Your current guess streak: {current}"

    sent = await message.reply_text(capsify(text))
    asyncio.create_task(auto_delete(sent))
    
