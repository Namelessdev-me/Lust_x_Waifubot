import math
from itertools import groupby
from pyrogram import Client,filters
from pyrogram.types import InlineKeyboardButton as IKB,InlineKeyboardMarkup as IKM
from . import user_collection,capsify,app
from .block import temp_block,block_cbq

@app.on_message(filters.command(["myslaves","collection"]))
async def myslaves(client,message,page=0):
 user_id=message.from_user.id
 if temp_block(user_id):return
 user=await user_collection.find_one({'id':user_id})
 if not user:
  await message.reply_text(capsify("You have not grabbed any slaves yet..."));return
 cmode=user.get('collection_mode','All')
 characters=[char for char in user['characters'] if cmode=='All' or char.get('rarity','')==cmode]
 characters=sorted(characters,key=lambda x:(x['anime'],x['id']))
 character_counts={k:len(list(v)) for k,v in groupby(characters,key=lambda x:x['id'])}
 unique_characters=list({character['id']:character for character in characters}.values())
 total_pages=max(1,math.ceil(len(unique_characters)/7))
 if page<0 or page>=total_pages:page=0
 myslaves_message=capsify(f"Collection - Page {page+1}/{total_pages}\n--------------------------------------\n\n")
 current_characters=unique_characters[page*7:(page+1)*7]
 for character in current_characters:
  count=character_counts[character['id']]
  myslaves_message+=f"♦️ {capsify(character['name'])} (x{count})\n   Anime: {character['anime']}\n   ID: {character['id']}\n   {character.get('rarity','')}\n\n"
 myslaves_message+="--------------------------------------\n"
 myslaves_message+=capsify(f"Myslaves Mode: {cmode}\n")
 total_count=len(unique_characters)
 myslaves_message+=capsify(f"Total Characters: {total_count}")
 inline_query=f"collection.{user_id}"
 if cmode!='All':inline_query+=f".{cmode}"
 keyboard=[[IKB(capsify(f"Inline ({total_count})"),switch_inline_query_current_chat=inline_query)],[IKB("🍹 Myslaves",switch_inline_query_current_chat=f"collection.{user_id}"),IKB("ANI 🎥",switch_inline_query_current_chat=f"vcollection.{user_id}")]]
 if total_pages>1:
  nav_buttons=[]
  if page>0:nav_buttons.append(IKB(capsify("◄"),callback_data=f"myslaves:{page-1}:{user_id}"))
  if page<total_pages-1:nav_buttons.append(IKB(capsify("►"),callback_data=f"myslaves:{page+1}:{user_id}"))
  keyboard.append(nav_buttons)
  skip_buttons=[]
  if page>4:skip_buttons.append(IKB(capsify("x5◀"),callback_data=f"myslaves:{page-5}:{user_id}"))
  if page<total_pages-5:skip_buttons.append(IKB(capsify("▶5x"),callback_data=f"myslaves:{page+5}:{user_id}"))
  keyboard.append(skip_buttons)
 keyboard.append([IKB(capsify("Close"),callback_data=f"myslaves:close_{user_id}")])
 markup=IKM(keyboard)
 if 'favorites' in user and user['favorites']:
  fav_character_id=user['favorites'][0]
  fav_character=next((c for c in user['characters'] if c['id']==fav_character_id),None)
  if fav_character and 'img_url' in fav_character:
   media=fav_character['img_url']
   try:
    await app.send_photo(message.chat.id,photo=media,caption=myslaves_message,reply_markup=markup,reply_to_message_id=message.id)
   except:
    await app.send_video(message.chat.id,video=media,caption=myslaves_message,reply_markup=markup,reply_to_message_id=message.id)
   return
 await message.reply_text(myslaves_message,reply_markup=markup)

@app.on_callback_query(filters.regex(r"myslaves:"))
@block_cbq
async def myslaves_callback(client,callback_query):
 data=callback_query.data
 if data.startswith("myslaves:close"):
  end_user=int(data.split('_')[1])
  if end_user==callback_query.from_user.id:
   await callback_query.answer()
   await callback_query.message.delete()
  else:
   await callback_query.answer(capsify("This is not your Myslaves"),show_alert=True)
  return
 _,page,user_id=data.split(':')
 page=int(page)
 user_id=int(user_id)
 if callback_query.from_user.id!=user_id:
  await callback_query.answer(capsify("This is not your Myslaves"),show_alert=True)
  return
 await myslaves(client,callback_query.message,page)
