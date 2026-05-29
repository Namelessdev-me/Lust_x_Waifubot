import random
import asyncio
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from . import collection, user_collection, group_user_totals_collection, top_global_groups_collection, app, capsify
from asyncio import Lock
from .watchers import character_watcher

message_counts = {}
spawn_locks = {}
spawned_characters = {}
chat_locks = {}

@app.on_message(filters.all & filters.group, group=character_watcher)
async def handle_message(_, message):
    chat_id = message.chat.id
    message_counts[chat_id] = message_counts.get(chat_id, 0) + 1

    chat_data = await group_user_totals_collection.find_one({'chat_id': chat_id})
    frequency = chat_data['message_frequency'] if chat_data and 'message_frequency' in chat_data else 100

    if chat_id in spawn_locks and spawn_locks[chat_id].locked():
        return

    if message_counts[chat_id] >= frequency:
        success = await spawn_character(chat_id)
        if success:
            message_counts[chat_id] = 0


async def spawn_character(chat_id):

    if chat_id not in spawn_locks:
        spawn_locks[chat_id] = Lock()

    async with spawn_locks[chat_id]:

        if chat_id in spawned_characters:
            return False

        chat_modes = await group_user_totals_collection.find_one({"chat_id": chat_id})

        if chat_modes is None:
            chat_modes = {"chat_id": chat_id, "character": True, "words": True, "maths": True}
            await group_user_totals_collection.update_one({"chat_id": chat_id}, {"$set": chat_modes}, upsert=True)

        if not chat_modes.get('character', True):
            return False

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

        
        rarity_enabled = {
            "⚪ Common":    True,
            "☘️ Medium":   True,
            "🔴 Rare":     True,
            "🟡 Legendary": True,
            "💋 Nude":      True,
            "🔮 Limited":   True,
            "🐦‍🔥 Exotic":  False,
            "🎐 Devine":    True,
            "💦 Wet":       True,
            "🎥 Animation": True
        }

        rarity_weights = {
            "⚪ Common":    55.0,
            "☘️ Medium":   22.0,
            "🔴 Rare":     12.0,
            "🟡 Legendary": 6.0,
            "💋 Nude":      2.5,
            "🔮 Limited":   1.5,
            "🐦‍🔥 Exotic":  0.0,
            "🎐 Devine":    0.1,
            "💦 Wet":    0.3,
            "🎥 Animation": 0.1
        }


        active_weights = {r: w for r, w in rarity_weights.items() if rarity_enabled.get(r, True)}

        all_characters = await collection.find({}).to_list(length=None)

        if not all_characters:
            return False


        valid_characters = [c for c in all_characters if c.get('rarity') in active_weights]

        if not valid_characters:
            # Fallback: agar koi bhi enabled rarity ka character na mile toh sab use karo
            valid_characters = all_characters

        weights = [active_weights.get(c.get('rarity', ''), 1.0) for c in valid_characters]
        character = random.choices(valid_characters, weights=weights, k=1)[0]

        spawned_characters[chat_id] = character

        caption = (
            f"🌬️ {capsify('A NEW CHARACTER HAS APPEARED!')} 🌊\n"
            f"{capsify('USE ')}/slave {capsify('(NAME) TO CLAIM IT.')}\n\n"
            f"🎐 {capsify('RARITY')}: {character['rarity']}\n"
            f"🍹 {capsify('NAME REVEAL')}: {capsify('100 EXLIX')}"
        )

        keyboard = [[InlineKeyboardButton(capsify("NAME"), callback_data=f"name_{character['id']}")]]
        markup = InlineKeyboardMarkup(keyboard)

        if character.get("type") == "video":
            await app.send_video(
                chat_id=chat_id,
                video=character['img_url'],
                caption=caption,
                reply_markup=markup,
                has_spoiler=True
            )
        else:
            await app.send_photo(
                chat_id=chat_id,
                photo=character['img_url'],
                caption=caption,
                reply_markup=markup,
                has_spoiler=True
            )

        asyncio.create_task(remove_spawn_after_timeout(chat_id, character, timeout=300))

        return True


async def remove_spawn_after_timeout(chat_id, character, timeout):

    await asyncio.sleep(timeout)

    if chat_id in spawned_characters and spawned_characters[chat_id] == character:

        keyboard = [[InlineKeyboardButton(capsify("HOW MANY TIME I FETCHED"), callback_data=f"count_{character['id']}")]]

        caption = capsify(
            f"❌ No One slaved ! 🏃‍♀️\n\n"
            f"🌬️ {capsify('NAME')}: {character['name']}\n"
            f"🎐 {capsify('ANIME')}: {character['anime']}\n"
            f"🍹 {capsify('RARITY')}: {character['rarity']}\n"
        )

        if character.get("type") == "video":
            await app.send_video(
                chat_id,
                video=character['img_url'],
                caption=caption,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await app.send_photo(
                chat_id,
                photo=character['img_url'],
                caption=caption,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        del spawned_characters[chat_id]


@app.on_message(filters.command("slave"))
async def guess(_, message):

    chat_id = message.chat.id
    user_id = message.from_user.id

    if chat_id not in chat_locks:
        chat_locks[chat_id] = Lock()

    async with chat_locks[chat_id]:

        args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None

        if not args or "()" in args or "&" in args:
            await message.reply_text(capsify("❌ INVALID INPUT."))
            return

        guess = args.strip().lower()

        if chat_id not in spawned_characters:
            await message.reply_text(capsify("❌ NO CHARACTER HAS SPAWNED YET."))
            return

        character = spawned_characters[chat_id]

        character_name = character['name'].strip().lower()
        name_parts = character_name.split()

        if guess not in name_parts:
            await message.reply_text(
                capsify(f"❌ INCORRECT NAME. '{guess.upper()}' DOES NOT MATCH.")
            )
            return

        user_data = await user_collection.find_one({'id': user_id})

        if not user_data:
            await user_collection.insert_one({
                'id': user_id,
                'balance': 0,
                'characters': [],
                'created_at': asyncio.get_event_loop().time()
            })

        await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})

        await group_user_totals_collection.update_one(
            {'user_id': user_id, 'group_id': chat_id},
            {'$inc': {'count': 1}},
            upsert=True
        )

        await top_global_groups_collection.update_one(
            {'group_id': chat_id},
            {'$inc': {'count': 1}, '$set': {'group_name': message.chat.title}},
            upsert=True
        )

        keyboard = [[InlineKeyboardButton(capsify("CHECK MYSLAVES"), switch_inline_query_current_chat=f"collection.{user_id}")]]

        success_message = capsify(
            f"✨ CONGRATULATIONS {message.from_user.first_name}!\n\n"
            f"🌬️ NAME: {character['name']}\n"
            f"🧧 ANIME: {character['anime']}\n"
            f"🪼 RARITY: {character['rarity']}\n\n"
            f"🕊️ CHARACTER ADDED TO YOUR COLLECTION!"
        )

        await message.reply_text(
            success_message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        del spawned_characters[chat_id]


@app.on_callback_query(filters.regex("^name_"))
async def handle_name_button(_, callback_query):

    chat_id = callback_query.message.chat.id
    character_id = callback_query.data.split("_")[1]

    character = spawned_characters.get(chat_id)

    if not character or str(character['id']) != character_id:
        await callback_query.answer("❌ Character not available.", show_alert=True)
        return

    user_id = callback_query.from_user.id

    user_data = await user_collection.find_one({'id': user_id})

    if not user_data:
        await user_collection.insert_one({
            'id': user_id,
            'balance': 0,
            'characters': [],
            'created_at': asyncio.get_event_loop().time()
        })
        user_balance = 0
    else:
        user_balance = int(user_data.get('balance', 0))

    new_balance = user_balance - 100

    await user_collection.update_one(
        {'id': user_id},
        {'$set': {'balance': new_balance}}
    )

    await callback_query.answer(
        f"🌬️ {character['name']}\n💰 -100 EXLIX\nBalance: {new_balance}",
        show_alert=True
    )


@app.on_callback_query(filters.regex("^count_"))
async def handle_count_button(_, callback_query):

    user_id = callback_query.from_user.id
    character_id = callback_query.data.split("_")[1]

    user_data = await user_collection.find_one({"id": user_id})

    if not user_data or "characters" not in user_data:
        await callback_query.answer(capsify("YOU DON'T OWN THIS CHARACTER."), show_alert=True)
        return

    count = sum(1 for char in user_data["characters"] if str(char["id"]) == character_id)

    await callback_query.answer(
        capsify(f"YOU HAVE {count} OF THIS CHARACTER."),
        show_alert=True
        )
        
