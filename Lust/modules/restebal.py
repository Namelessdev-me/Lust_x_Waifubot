from pyrogram import Client, filters
from pyrogram.types import Message
from . import app, capsify, user_collection
import OWNER_ID


@app.on_message(filters.command("resetbal") & OWNER_ID)
async def reset_balance(client: Client, message: Message):

    if not message.from_user:
        return

    args = message.text.split(maxsplit=2)

    
    if len(args) < 2:
        return await message.reply_text(
            capsify(
                "USAGE:\n"
                "/restebal all\n"
                "/restebal <userid> <username>"
            )
        )

    
    if args[1].lower() == "all":
        result = await user_collection.update_many(
            {},
            {
                "$set": {
                    "balance": 0,
                    "saved_amount": 0,
                    "loan_amount": 0
                }
            }
        )

        return await message.reply_text(
            capsify(
                f"✅ ALL USER BALANCE RESET\n\n"
                f"👥 USERS AFFECTED: {result.modified_count}"
            )
        )

  
    try:
        target_id = int(args[1])
    except ValueError:
        return await message.reply_text(
            capsify("INVALID USER ID.")
        )

    target_name = args[2] if len(args) > 2 else "Unknown"

    user = await user_collection.find_one({"id": target_id})
    if not user:
        return await message.reply_text(
            capsify("USER NOT FOUND IN DATABASE.")
        )

    await user_collection.update_one(
        {"id": target_id},
        {
            "$set": {
                "balance": 0,
                "saved_amount": 0,
                "loan_amount": 0
            }
        }
    )

    await message.reply_text(
        capsify(
            f"✅ USER BALANCE RESET SUCCESSFUL\n\n"
            f"👽 USER : {target_name}\n"
            f"🪪 ID   : {target_id}"
        )
    )
