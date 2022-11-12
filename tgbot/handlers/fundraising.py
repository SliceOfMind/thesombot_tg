from aiogram import Dispatcher
from aiogram.types import CallbackQuery
import aiogram.utils.markdown as md

import tgbot.misc.callbacks as callbacks
import tgbot.keyboards.inline as inline_keyboards
from tgbot.handlers.main_menu import show_balance
from tgbot.services.db.database import Database
from tgbot.services.custom_broadcasters import MultilingualTextBroadcaster


async def show_fundraising_book_menu(call: CallbackQuery, callback_data: dict):
    _ = call.bot.get('_')
    db: Database = call.bot.get('database')

    user = await db.users_worker.get_user_by_telegram_id(call.from_user.id)
    is_user_subscriber = user['subscribe_status_id'] == 3
    book = await db.books_worker.select(record_id=callback_data['book_id'])
    is_purchased = await db.books_worker.is_user_purchased_book(user['id'], book['id'])
    
    if book['is_done']:
        price = book['price_after_done']
    else:
        if is_user_subscriber:
            price = book['price_for_sub']
        else:
            price = book['price_common']

    if book['collected_sum'] > book['goal_sum']:
        progress = _('Формат прогресса').format(percent=100)
    else:
        progress = _('Формат прогресса').format(percent=round((book['collected_sum'] / book['goal_sum']) * 100))

    if is_user_subscriber and not user['show_progress']:
        progress = ''

    text = _('Меню книги фандрайзинга').format(
        title=md.escape_md(book['name']),
        description=md.escape_md(book['description']),
        start=md.escape_md(book['start_date']),
        end=md.escape_md(book['end_date']),
        progress=md.escape_md(progress),
        price=md.escape_md(price)
    )
    keyboard = inline_keyboards.get_fundraising_book_keyboard(_, is_purchased, is_user_subscriber, book, price)
    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


async def buy_fundraising_book(call: CallbackQuery, callback_data: dict):
    _ = call.bot.get('_')
    db: Database = call.bot.get('database')

    user = await db.users_worker.get_user_by_telegram_id(call.from_user.id)

    if int(callback_data['price']) > int(user['balance']):
        await call.answer(_('Ошибка недостаточно баланса'), show_alert=True)
        await show_balance(call, {'payload': callback_data['book_id']})
        return

    await db.books_worker.add_purchased_book(user['id'], callback_data['book_id'])
    await db.books_worker.increase_collected_sum(callback_data['book_id'], callback_data['price'])
    await db.users_worker.update_balance(call.from_user.id, f'-{callback_data["price"]}')

    book = await db.books_worker.select(record_id=callback_data['book_id'])
    if (not book['is_done']) and book['collected_sum'] >= book['goal_sum']:
        await db.books_worker.update_is_done(book['id'], True)
        users = await db.books_worker.get_telegram_ids_of_users_who_purchased_book(book['id'])
        _('Уведомление о завершении сбора на книгу')  # So that pybabel can find string
        _('Уведомление о доступности книги из фандрайзинга')  # So that pybabel can find string
        await MultilingualTextBroadcaster(
            chats=[user['telegram_id'] for user in users],
            text='Уведомление о завершении сбора на книгу',
            text_kwargs={'title': book['name']},
            bot=call.bot,
            database=db,
            config=call.bot.get('config'),
            reply_markup_callback=inline_keyboards.get_close_keyboard
        ).run()

    await call.answer(_('Уведомление о покупке книги'), show_alert=True)
    await show_fundraising_book_menu(call, callback_data)


async def change_show_progress(call: CallbackQuery, callback_data: dict):
    _ = call.bot.get('_')
    db: Database = call.bot.get('database')

    show_progress = await db.users_worker.change_show_progress(call.from_user.id)
    if show_progress:
        await call.answer(_('Уведомление о включении отображения прогресса'), show_alert=True)
    else:
        await call.answer(_('Уведомление о выключении отображения прогресса'), show_alert=True)

    await show_fundraising_book_menu(call, callback_data)


def register_fundraising(dp: Dispatcher):
    dp.register_callback_query_handler(show_fundraising_book_menu, callbacks.fundraising_book.filter())
    dp.register_callback_query_handler(buy_fundraising_book, callbacks.buy_fundraising_book.filter())
    dp.register_callback_query_handler(change_show_progress, callbacks.change_show_progress.filter())
