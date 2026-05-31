from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler
from Lust import application
#from .cmode import cmode_callback
from Lust.utils.button import button_click as bc
#from .myslaves import myslaves_callback as hc
from .info import check
#from .sgift import confirm_gift, cancel_gift
from .trade import confirm_trade, cancel_trade
from .rps import rps_button 
#from .start import button
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
    elif data in ('rock', 'paper', 'scissors', 'play_again'):
        await rps_button(update, context)
        
application.add_handler(CallbackQueryHandler(cbq, pattern='.*'))
