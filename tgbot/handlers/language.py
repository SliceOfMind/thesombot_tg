from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery

import tgbot.misc.callbacks as callbacks
from tgbot.handlers.main_menu import show_main_menu
from tgbot.services.db.database import Database


async def choose_language(call: CallbackQuery, callback_data: dict, state: FSMContext):
    db: Database = call.bot.get('database')
    _ = call.bot.get('_')

    await db.users_worker.update_language(call.from_user.id, callback_data['code'])
    await call.answer(_('Уведомление о смене языка', locale=callback_data['code']))

    await show_main_menu(call, {'locale': callback_data['code']}, state)


def register_language(dp: Dispatcher):
    dp.register_callback_query_handler(choose_language, callbacks.languages.filter())
