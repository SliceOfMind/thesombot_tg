from aiogram import Dispatcher
from aiogram.types import Update
from aiogram.utils.exceptions import MessageCantBeEdited


async def cant_be_edited(update: Update, exception):
    _ = update.bot.get('_')

    if update.callback_query:
        await update.callback_query.answer(_('Ошибка устаревшее меню'), show_alert=True)


def register_errors(dp: Dispatcher):
    dp.register_errors_handler(cant_be_edited, exception=MessageCantBeEdited)
