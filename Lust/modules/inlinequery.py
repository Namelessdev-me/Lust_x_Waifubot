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
InlineQueryResultVideo as IQV
)

from . import user_collection, collection, application, db, capsify
from .block import block_inl_ptb

lock = asyncio.Lock()

db.characters.create_index([('id', DESCENDING)])
db.characters.create_index([('anime', DESCENDING)])
db.characters.create_index([('img_url', DESCENDING)])

db.user_collection.create_index([('characters.id', DESCENDING)])

all_characters_cache = TTLCache(maxsize=10000, ttl=36000)

RARITY_MAP={
1:"⚪ Common",
2:"☘️ Medium",
3:"🔴 Rare",
4:"🟡 Legendary",
5:"💋 Nude",
6:"🔮 Limited",
7:"🐦‍🔥 Exotic",
8:"🎐 Devine",
9:"💦 Wet",
10:"🎥 Animation"
}

CATEGORY_MAP={
'🎒':'🎒 𝑪𝒍𝒂𝒔𝒔𝒓𝒐𝒐𝒎 𝑸𝒖𝒆𝒆𝒏 🎒',
'💉':'💉 𝑾𝒉𝒊𝒕𝒆 𝑮𝒓𝒂𝒄𝒆 💉',
'🧹':'🧹 𝑪𝒉𝒂𝒓𝒎 𝑴𝒂𝒊𝒅𝒆𝒏 🧹',
'🐰':'🐰 𝑴𝒐𝒐𝒏𝒍𝒊𝒕 𝑩𝒐𝒖𝒏𝒄𝒆 🐰',
'👘':'👘 𝑺𝒂𝒌𝒖𝒓𝒂 𝑮𝒓𝒂𝒄𝒆 👘',
'💍':'💍 𝑭𝒐𝒓𝒆𝒗𝒆𝒓 𝑩𝒍𝒊𝒔𝒔 💍',
'🎊':'🎊 𝑽𝒊𝒃𝒆 𝑬𝒏𝒆𝒓𝒈𝒚 🎊',
'🚓':'🚓 𝑱𝒖𝒔𝒕𝒊𝒄𝒆 𝑬𝒏𝒄𝒉𝒂𝒏𝒕𝒓𝒆𝒔𝒔 🚓',
'🥻':'🥻 𝑬𝒕𝒉𝒆𝒓𝒆𝒂𝒍 𝑮𝒆𝒎 🥻',
'🕷':'🕷 𝑵𝒆𝒕 𝑺𝒐𝒓𝒄𝒆𝒓𝒆𝒔𝒔 🕷',
'🏜':'🏜 𝑺𝒂𝒏𝒅𝒔 𝑬𝒎𝒑𝒓𝒆𝒔𝒔 🏜',
'⚜️':'⚜️ 𝑺𝒂𝒄𝒓𝒆𝒅 𝑶𝒂𝒕𝒉 ⚜️',
'🩸':'🩸 𝑵𝒐𝒄𝒕𝒖𝒓𝒏𝒂𝒍 𝑹𝒐𝒔𝒆 🩸',
'🕊️':'🕊️ 𝑾𝒊𝒏𝒈𝒔 𝒐𝒇 𝑭𝒂𝒕𝒆 🕊️',
'☃️':'☃️ 𝑺𝒏𝒐𝒘𝒇𝒂𝒍𝒍 𝑬𝒍𝒍𝒆 ☃️',
'💞':'💞 𝑯𝒆𝒂𝒓𝒕𝒔𝒐𝒏𝒈 𝑫𝒖𝒄𝒉𝒆𝒔𝒔 💞',
'🏖':'🏖 𝑺𝒖𝒏𝒌𝒊𝒔𝒔 𝑺𝒆𝒓𝒆𝒏𝒂𝒅𝒆 🏖',
'🎃':'🎃 𝑺𝒑𝒆𝒍𝒍𝒃𝒐𝒖𝒏𝒅 𝑾𝒊𝒕𝒄𝒉 🎃',
'🎮':'🎮 𝑮𝒂𝒎𝒆 𝑮𝒐𝒅𝒅𝒆𝒔𝒔 🎮'
}

@block_inl_ptb
async def inlinequery(update:Update,context:CallbackContext):

 query=update.inline_query.query.strip()

 if query.startswith("collection.") or query.startswith("vcollection."):

  parts=query.split(".")
  user_id=int(parts[1])
  video_only=query.startswith("vcollection.")

  user=await user_collection.find_one({'id':user_id})

  if not user:
   await update.inline_query.answer([],cache_time=1)
   return

  results=[]

  for char in user.get("characters",[]):

   character=await collection.find_one(
   {"id":char["id"]},
   {'name':1,'anime':1,'img_url':1,'id':1,'rarity':1,'type':1,'category':1}
   )

   if not character:
    continue

   if video_only and character.get("type")!="video":
    continue

   rarity=RARITY_MAP.get(character.get("rarity"),character.get("rarity"))
   category=CATEGORY_MAP.get(character.get("category"),"")

   caption=(
   "✦ 𝗢𝘄𝗢! 𝗖𝗵𝗲𝗰𝗸 𝗢𝘂𝘁 𝗧𝗵𝗶𝘀 𝗖𝗵𝗮𝗿𝗮𝗰𝗧𝗲𝗿! ✦\n\n"
   f"『 {character['anime']} 』\n"
   f"✧ {character['id']}: {character['name']}\n"
   f"{category}\n"
   f"({rarity})"
   )

   keyboard=[[IKB(
   capsify("How many I have ❓"),
   callback_data=f"check_{update.inline_query.from_user.id}_{character['id']}"
   )]]

   reply_markup=IKM(keyboard)

   if character.get("type")=="video":

    results.append(IQV(
    id=str(character["id"]),
    video_url=character["img_url"],
    mime_type="video/mp4",
    thumbnail_url=character["img_url"],
    title=character["name"],
    caption=caption,
    reply_markup=reply_markup
    ))

   else:

    results.append(IQP(
    id=f"{character['id']}_{time.time()}",
    photo_url=character["img_url"],
    thumbnail_url=character["img_url"],
    caption=caption,
    reply_markup=reply_markup
    ))

  await update.inline_query.answer(results[:50],cache_time=5)
  return

 offset=int(update.inline_query.offset) if update.inline_query.offset else 0
 results_per_page=15
 start_index=offset
 end_index=offset+results_per_page

 if not query:

  if 'all_characters' in all_characters_cache:
   all_characters=all_characters_cache['all_characters']
  else:
   all_characters=await collection.find({},{
   'name':1,'anime':1,'img_url':1,'id':1,'rarity':1,'type':1,'category':1
   }).to_list(length=None)

   all_characters_cache['all_characters']=all_characters

 else:

  regex=re.compile(query,re.IGNORECASE)

  all_characters=await collection.find(
  {"$or":[{"name":regex},{"anime":regex}]}
  ).to_list(length=None)

 characters=list(all_characters)[start_index:end_index]

 results=[]

 for character in characters:

  rarity=RARITY_MAP.get(character.get("rarity"),character.get("rarity"))
  category=CATEGORY_MAP.get(character.get("category"),"")

  caption=(
  "✦ 𝗢𝘄𝗢! 𝗖𝗵𝗲𝗰𝗸 𝗢𝘂𝘁 𝗧𝗵𝗶𝘀 𝗖𝗵𝗮𝗿𝗮𝗰𝗧𝗲𝗿! ✦\n\n"
  f"『 {character['anime']} 』\n"
  f"✧ {character['id']}: {character['name']}\n"
  f"{category}\n"
  f"({rarity})"
  )

  keyboard=[[IKB(
  capsify("How many I have ❓"),
  callback_data=f"check_{update.inline_query.from_user.id}_{character['id']}"
  )]]

  reply_markup=IKM(keyboard)

  if character.get("type")=="video":

   results.append(IQV(
   id=str(character["id"]),
   video_url=character["img_url"],
   mime_type="video/mp4",
   thumbnail_url=character["img_url"],
   title=character["name"],
   caption=caption,
   reply_markup=reply_markup
   ))

  else:

   results.append(IQP(
   id=f"{character['id']}_{time.time()}",
   photo_url=character["img_url"],
   thumbnail_url=character["img_url"],
   caption=caption,
   reply_markup=reply_markup
   ))

 next_offset=str(end_index) if len(characters)==results_per_page else ""

 await update.inline_query.answer(
 results,
 next_offset=next_offset,
 cache_time=5
 )

application.add_handler(
InlineQueryHandler(inlinequery,block=False)
 )
