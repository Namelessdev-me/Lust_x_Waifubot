from pyrogram import filters
from . import collection,user_collection,sudo_filter,app

LOG_CHAT_ID=-1002992299647

async def send_media(message,media,caption):
    try: await message.reply_photo(photo=media,caption=caption);return
    except: pass
    try: await message.reply_video(video=media,caption=caption);return
    except: pass
    try: await message.reply_animation(animation=media,caption=caption);return
    except: pass
    await message.reply_document(document=media,caption=caption)

async def give_character(receiver_id,character_id):
    character=await collection.find_one({'id':character_id})
    if not character: raise ValueError("Character not found.")
    await user_collection.update_one({'id':receiver_id},{'$push':{'characters':character}})
    media=character['img_url']
    caption=(f"Successfully Given To {receiver_id}\nInformation As Follows\n"
             f"🫂 Anime: {character['anime']}\n💕 Name: {character['name']}\n"
             f"🍿 ID: {character['id']}\n🌟 Rarity: {character.get('rarity','Unknown')}")
    return media,caption

@app.on_message(filters.command(["addchar"]) & sudo_filter)
async def give_character_command(client,message):
    if not message.reply_to_message:
        await message.reply_text("Reply to a user to give character.");return
    try:
        character_id=str(message.text.split()[1])
        receiver_id=message.reply_to_message.from_user.id
        receiver_name=message.reply_to_message.from_user.first_name
        giver_name=message.from_user.first_name
        media,caption=await give_character(receiver_id,character_id)
        await send_media(message,media,caption)
        await client.send_message(LOG_CHAT_ID,f"{giver_name} gave character {character_id} to {receiver_name}")
    except IndexError: await message.reply_text("Provide character ID.")
    except ValueError as e: await message.reply_text(str(e))
    except Exception as e:
        print(e);await message.reply_text("Error while processing command.")

async def add_all_characters_for_user(user_id):
    user=await user_collection.find_one({'id':user_id})
    if not user: return f"User {user_id} not found."
    all_chars=await collection.find({}).to_list(length=None)
    existing={c['id'] for c in user['characters']}
    new_chars=[c for c in all_chars if c['id'] not in existing]
    if not new_chars: return f"No new characters for {user_id}"
    await user_collection.update_one({'id':user_id},{'$push':{'characters':{'$each':new_chars}}})
    return f"Added all characters to {user_id}"

@app.on_message(filters.command(["ad"]) & sudo_filter)
async def add_characters_command(client,message):
    if not message.reply_to_message:
        await message.reply_text("Reply to user to add characters.");return
    uid=message.reply_to_message.from_user.id
    res=await add_all_characters_for_user(uid)
    await message.reply_text(res)

async def kill_character(receiver_id,character_id):
    character=await collection.find_one({'id':character_id})
    if not character: raise ValueError("Character not found.")
    await user_collection.update_one({'id':receiver_id},{'$pull':{'characters':{'id':character_id}}})
    return f"Removed character {character_id} from {receiver_id}"

@app.on_message(filters.command(["blank"]) & sudo_filter)
async def remove_character_command(client,message):
    try:
        args=message.text.split()
        if len(args)==3:
            receiver_id=int(args[1]);character_id=str(args[2])
        elif message.reply_to_message and len(args)==2:
            receiver_id=message.reply_to_message.from_user.id;character_id=str(args[1])
        else:
            await message.reply_text("Usage: /blank <user_id> <char_id> or reply with /blank <char_id>");return
        res=await kill_character(receiver_id,character_id)
        await message.reply_text(res)
    except Exception as e:
        print(e);await message.reply_text("Error while removing character.")
