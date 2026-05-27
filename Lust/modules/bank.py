from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime, timedelta
import math
from . import add, deduct, show, abank, dbank, sbank, user_collection, app, capsify
from .block import block_dec, temp_block

async def handle_error(client: Client, message: Message, error: Exception):
    error_message = f"An error occurred: {str(error)}"
    await message.reply_text(capsify(error_message))
    print(f"Error: {error}")

@block_dec
async def save(client: Client, message: Message):
    try:
        amount = int(message.command[1])
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
    except (IndexError, ValueError) as e:
        await handle_error(client, message, e)
        return

    user_id = message.from_user.id
    if temp_block(user_id):
        return
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1})

    if user_data:
        balance_amount = int(user_data.get('balance', 0))

        if amount > balance_amount:
            await message.reply_text(capsify("Insufficient balance to save this amount."))
            return

        await deduct(user_id, amount)
        await abank(user_id, amount)

        await message.reply_text(capsify(f"You saved {amount} Exlix in your bank account."))
    else:
        await message.reply_text(capsify("User data not found."))

@block_dec
async def withdraw(client: Client, message: Message):
    try:
        amount = int(message.command[1])
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
    except (IndexError, ValueError) as e:
        await handle_error(client, message, e)
        return

    user_id = message.from_user.id
    if temp_block(user_id):
        return
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1, 'saved_amount': 1})

    if user_data:
        saved_amount = int(user_data.get('saved_amount', 0))

        if amount > saved_amount:
            await message.reply_text(capsify("Insufficient saved amount to withdraw."))
            return

        await add(user_id, amount)
        await dbank(user_id, amount)

        await message.reply_text(capsify(f"You withdrew {amount} Exlix from your bank account."))
    else:
        await message.reply_text(capsify("User data not found."))

@block_dec
async def loan(client: Client, message: Message):
    try:
        loan_amount = int(message.command[1])
        if loan_amount <= 0 or loan_amount > 400000:
            raise ValueError("Amount must be between 1 and 400000.")
    except (IndexError, ValueError) as e:
        await handle_error(client, message, e)
        return

    user_id = message.from_user.id
    if temp_block(user_id):
        return
    user_data = await user_collection.find_one(
        {'id': user_id},
        projection={'balance': 1, 'saved_amount': 1, 'loan_amount': 1, 'loan_due_date': 1, 'last_loan_date': 1}
    )

    if user_data:
        current_time = datetime.now()
        last_loan_date = user_data.get('last_loan_date')


        if last_loan_date:
            days_since_last_loan = (current_time - last_loan_date).days
            if days_since_last_loan < 7:
                await message.reply_text(capsify(f"You can only take a loan once every 7 days. Try again in {7 - days_since_last_loan} days."))
                return


        if 'loan_amount' in user_data and user_data['loan_amount'] > 0:
            loan_due_date = user_data.get('loan_due_date')

            if current_time > loan_due_date:
                overdue_hours = (current_time - loan_due_date).total_seconds() / 3600
                penalty = math.ceil(overdue_hours) * (int(user_data['loan_amount']) * 0.05)
            else:
                penalty = 0

            total_deducted = int(user_data['balance']) + penalty
            await user_collection.update_one({'id': user_id}, {'$set': {'balance': 0, 'saved_amount': 0, 'loan_amount': 0}})
            log_message = f"User {message.from_user.first_name} ({user_id}) tried to exploit the loan system. Deducted balance and penalty: {total_deducted} Exlix."
            await client.send_message(-1003551781050, capsify(log_message))
            await message.reply_text(capsify("You tried to exploit the loan system. Your balance and saved amount have been reset to 0 as a penalty."))
            return


        loan_due_date = current_time + timedelta(days=10)

        new_balance = int(user_data.get('balance', 0)) + loan_amount
        await user_collection.update_one(
            {'id': user_id},
            {'$set': {'loan_amount': loan_amount, 'loan_due_date': loan_due_date, 'last_loan_date': current_time}}
        )
        await add(user_id, loan_amount)

        await message.reply_text(capsify(f"You successfully took a loan of {loan_amount} Exlix. You must repay it within 10 days to avoid a penalty."))
        log_message = f"Loan: +{loan_amount} Exlix | User ID: {user_id} | Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
        await client.send_message(-1003551781050, capsify(log_message))
    else:
        await message.reply_text(capsify("User data not found."))

@block_dec
async def repay(client: Client, message: Message):
    try:
        repayment_amount = int(message.command[1])
        if repayment_amount <= 0:
            raise ValueError("Amount must be greater than zero.")
    except (IndexError, ValueError) as e:
        await handle_error(client, message, e)
        return

    user_id = message.from_user.id
    if temp_block(user_id):
        return
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1, 'loan_amount': 1, 'loan_due_date': 1})

    if user_data:
        loan_amount = user_data.get('loan_amount', 0)
        loan_due_date = user_data.get('loan_due_date')
        current_time = datetime.now()

        if repayment_amount > loan_amount:
            await message.reply_text(capsify("Repayment amount cannot exceed the loan amount."))
            return

        if current_time > loan_due_date:
            overdue_hours = (current_time - loan_due_date).total_seconds() / 3600
            penalty = math.ceil(overdue_hours) * (loan_amount * 0.05)
            repayment_amount += penalty
            await message.reply_text(capsify(f"You have a penalty of {penalty:.2f} Exlix due to late repayment."))

        new_loan_amount = loan_amount - repayment_amount

        await user_collection.update_one({'id': user_id}, {'$set': {'loan_amount': new_loan_amount}})
        await deduct(user_id, repayment_amount)

        await message.reply_text(capsify(f"You successfully repaid {repayment_amount} Exlix of your loan."))
    else:
        await message.reply_text(capsify("User data not found."))

@app.on_message(filters.command("loan"))
async def loan_handler(client: Client, message: Message):
    await loan(client, message)

@app.on_message(filters.command("save"))
async def save_handler(client: Client, message: Message):
    await save(client, message)

@app.on_message(filters.command("repay"))
async def repay_handler(client: Client, message: Message):
    await repay(client, message)

@app.on_message(filters.command("withdraw"))
async def withdraw_handler(client: Client, message: Message):
    await withdraw(client, message)
