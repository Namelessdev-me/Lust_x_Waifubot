from pyrogram import filters
from . import app, capsify, collection
from .block import block_dec, temp_block


RARITY_LIST = [
    ("⚪ Common",    55.0,  "Most common slaves. Easy to collect."),
    ("☘️ Medium",   22.0,  "A step above common. Still findable."),
    ("🔴 Rare",     12.0,  "Hard to find. Worth keeping."),
    ("🟡 Legendary", 6.0,  "Very rare. Flex worthy."),
    ("💋 Nude",      2.5,  "Exclusive & spicy. Hard to get."),
    ("🔮 Limited",   1.5,  "Limited supply. Trade carefully."),
    ("🐦‍🔥 Exotic",  0.0,  "Almost impossible. Extremely valuable."),
    ("💦 Wet",       0.3,  "Ultra rare. Only the lucky find these."),
    ("🎐 Devine",    0.1,  "The rarest of all. 0.1% spawn chance!"),
]


@app.on_message(filters.command(["rarity", "rarities"]))
@block_dec
async def rarity_info(client, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    # Count per rarity in DB
    rarity_counts = {}
    all_chars = await collection.find({}, {"rarity": 1}).to_list(length=None)
    for char in all_chars:
        r = char.get("rarity", "Unknown")
        rarity_counts[r] = rarity_counts.get(r, 0) + 1

    total_chars = len(all_chars)

    lines = [
        "✨ ʀᴀʀɪᴛʏ ʟɪꜱᴛ\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
    ]

    for rarity, chance, desc in RARITY_LIST:
        count = rarity_counts.get(rarity, 0)
        lines.append(
            f"{rarity}\n"
            f"  📊 Spawn : {chance}%\n"
            f"  🗂 In DB  : {count} slaves\n"
            f"  💬 {desc}\n"
        )

    lines.append(f"━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"📦 Total Slaves in DB: {total_chars}")

    await message.reply_text(capsify("\n".join(lines)))
