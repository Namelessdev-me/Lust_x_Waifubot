from datetime import datetime
from Lust import user_collection
from . import capsify,app
from .block import block_dec,temp_block,block_cbq
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup as IKM,InlineKeyboardButton as IKB

async def safe_edit(msg, text):
    try:
        await msg.edit_text(text)
    except Exception as e1:
        try:
            await msg.edit_caption(text)
        except Exception as e2:
            try:
                await msg.reply(text)
            except:
                pass

@app.on_message(filters.command("gift"))
@block_dec
async def gift(client,message):
 sender_id=message.from_user.id
 if temp_block(sender_id):return
 if not message.reply_to_message:
  await message.reply(capsify("Reply to a user to gift a character!"));return
 receiver_id=message.reply_to_message.from_user.id
 if sender_id==receiver_id:
  await message.reply(capsify("You can't gift a character to yourself!"));return
 if len(message.command)!=2:
  await message.reply(capsify("Provide a character ID!"));return

 character_id=message.command[1]
 sender=await user_collection.find_one({'id':sender_id})

 if not sender:
  sender={'id':sender_id,'characters':[],'daily_gift_count':0,'last_reset':None}
  await user_collection.insert_one(sender)

 last_reset=sender.get('last_reset')
 daily_gift_count=sender.get('daily_gift_count',0)

 if not last_reset or datetime.fromisoformat(last_reset).date()<datetime.utcnow().date():
  daily_gift_count=0
  await user_collection.update_one({'id':sender_id},{'$set':{'daily_gift_count':0,'last_reset':datetime.utcnow().isoformat()}})

 if daily_gift_count>=10:
  await message.reply(capsify("Daily gift limit reached!"));return

 character=next((c for c in sender.get('characters',[]) if str(c.get('id'))==str(character_id)),None)

 if not character:
  await message.reply(capsify(f"You don't have character {character_id}!"));return

 media=character.get("img_url","")
 inline_query=f"collection.{sender_id}"

 if media.endswith((".mp4",".gif",".webm",".mkv")):
  inline_query=f"vcollection.{sender_id}"

 gifts_left=10-daily_gift_count

 msg=(f"{capsify('🎁 CONFIRM GIFTING')}\n\n"
      f"{capsify('♦️ NAME:')} {capsify(character['name'])}\n"
      f"{capsify('🧧 ANIME:')} {capsify(character['anime'])}\n"
      f"{capsify('🆔:')} {character['id']}\n"
      f"{capsify('🌟:')} {character.get('rarity','🔮 LIMITED')}\n\n"
      f"{capsify('GIFTS LEFT:')} {gifts_left}")

 keyboard=IKM([[IKB("🔎 INLINE",switch_inline_query_current_chat=inline_query)],
               [IKB("✅ CONFIRM",callback_data=f"con_gift:{sender_id}:{character_id}:{receiver_id}"),
                IKB("❌ CANCEL",callback_data=f"can_gift:{sender_id}")]])

 await message.reply(msg, reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"^(con_gift|can_gift):"))
@block_cbq
async def gift_callback(client, query):

 data=query.data.split(":")
 action=data[0]
 sender_id=int(data[1])

 if query.from_user.id!=sender_id:
  await query.answer("This is not for you!",show_alert=True);return

 if action=="can_gift":
  await query.answer("Gift cancelled!", show_alert=False)
  await safe_edit(query.message, capsify("❌ GIFT CANCELED SUCCESSFULLY"))
  return

 if action=="con_gift":

  if len(data)!=4:
   await query.answer("Invalid data",show_alert=True);return

  character_id=data[2]
  receiver_id=int(data[3])

  sender=await user_collection.find_one({'id':sender_id})

  if not sender:
   await query.answer("Sender data not found!", show_alert=True)
   await safe_edit(query.message, capsify("❌ SENDER DATA NOT FOUND"))
   return

  character=next((c for c in sender.get('characters',[]) if str(c.get('id'))==str(character_id)),None)

  if not character:
   await query.answer("Character not found!", show_alert=True)
   await safe_edit(query.message, capsify("❌ CHARACTER NOT FOUND"))
   return

  # exploit protection
  new_sender_chars=[c for c in sender.get('characters',[]) if str(c['id'])!=str(character_id)]

  if len(new_sender_chars)==len(sender.get('characters',[])):
   await query.answer("Character already gifted!", show_alert=True)
   await safe_edit(query.message, capsify("⚠️ CHARACTER ALREADY GIFTED"))
   return

  await user_collection.update_one({'id':sender_id},{'$set':{'characters':new_sender_chars}})

  receiver=await user_collection.find_one({'id':receiver_id})

  if receiver:
   await user_collection.update_one({'id':receiver_id},{'$push':{'characters':character}})
  else:
   await user_collection.insert_one({'id':receiver_id,'characters':[character]})

  sender=await user_collection.find_one({'id':sender_id})
  daily_gift_count=sender.get('daily_gift_count',0)+1

  await user_collection.update_one({'id':sender_id},{'$set':{'daily_gift_count':daily_gift_count}})

  success_msg=(f"{capsify('🎁 GIFT SENT SUCCESSFULLY')}\n\n"
               f"{capsify('♦️ NAME:')} {capsify(character['name'])}\n"
               f"{capsify('🧧 ANIME:')} {capsify(character['anime'])}\n"
               f"{capsify('🆔:')} {character['id']}\n"
               f"{capsify('🌟:')} {character.get('rarity','🔮 LIMITED')}\n\n"
               f"{capsify('GIFTS LEFT:')} {10-daily_gift_count}")

  await query.answer("✅ Gift sent!", show_alert=False)
  await safe_edit(query.message, success_msg)
  
