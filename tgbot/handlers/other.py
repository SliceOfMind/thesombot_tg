from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import ChatMemberUpdated, CallbackQuery
from aiogram.utils.exceptions import MessageCantBeDeleted

from tgbot.handlers.main_menu import (show_main_menu, show_balance, show_vote_menu, show_library_menu,
                                      show_subscribes_menu)
from tgbot.services.db.database import Database
import tgbot.misc.callbacks as callbacks
import tgbot.keyboards.inline as inline_keyboards


async def block_check(chat_member: ChatMemberUpdated):
    status = chat_member.new_chat_member.status
    if status == 'kicked':
        is_blocked = True
    elif status == 'member':
        is_blocked = False
    else:
        return

    db: Database = chat_member.bot.get('database')
    await db.users_worker.update_is_block(chat_member.from_user.id, is_blocked)


async def close_message(call: CallbackQuery, callback_data: dict):
    _ = call.bot.get('_')

    is_final = bool(callback_data['is_final'])
    if not is_final:
        await call.message.edit_reply_markup(inline_keyboards.get_close_keyboard(_))
        await call.answer(_('Предупреждение об удалении сообщения'), show_alert=True)
        return

    try:
        await call.message.delete()
    except MessageCantBeDeleted:
        await call.answer(_('Ошибка сообщение не может быть закрыто'), show_alert=True)
    else:
        await call.answer()


async def show_book_isnt_available(call: CallbackQuery):
    _ = call.bot.get('_')

    await call.answer(_('Ошибка книга недоступна для скачивания'), show_alert=True)


async def cancel_state(call: CallbackQuery, callback_data: dict, state: FSMContext):
    if callback_data['to'] == 'library':
        await show_library_menu(call, state)
        return

    await state.finish()
    match callback_data['to']:
        case 'main_menu':
            await show_main_menu(call, {}, state)
        case 'balance':
            await show_balance(call, {'payload': ''})
        case 'vote':
            await show_vote_menu(call)
        case 'subscribes':
            await show_subscribes_menu(call)
        case _:
            await show_main_menu(call, {}, state)


def register_other(dp: Dispatcher):
    dp.register_my_chat_member_handler(block_check, state='*')
    dp.register_callback_query_handler(close_message, callbacks.close.filter(), state='*')
    dp.register_callback_query_handler(cancel_state, callbacks.cancel.filter(), state='*')
    dp.register_callback_query_handler(show_book_isnt_available, text='book_isnt_available', state='*')
