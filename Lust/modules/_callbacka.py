from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler
from Lust import application
from Lust.utils.button import button_click as bc
from .info import check
from .trade import confirm_trade, cancel_trade
from .rps import rps_button
from .sgift import gift_callback
from .kidnap import kidnap_callback
from .block import block_cbq_ptb

@block_cbq_ptb
async def cbq(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    if data.startswith('check_'):
        await check(update, context)
    elif data.startswith('confirm_trade'):
        await confirm_trade(update, context)
    elif data.startswith('cancel_trade'):
        await cancel_trade(update, context)
    elif data.startswith('con_gift') or data.startswith('can_gift'):
        await gift_callback(update, context)
    elif data.startswith('kidnap:'):
        await kidnap_callback(update, context)
    elif data in ('rock', 'paper', 'scissors', 'play_again'):
        await rps_button(update, context)

application.add_handler(CallbackQueryHandler(cbq, pattern='.*'))
