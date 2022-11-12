import math

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message
import aiogram.utils.markdown as md

import tgbot.misc.states as states
import tgbot.misc.callbacks as callbacks
import tgbot.keyboards.inline as inline_keyboards
from tgbot.config import Config
from tgbot.handlers.main_menu import show_library_menu
from tgbot.services.db.database import Database


async def start_year_input(call: CallbackQuery, state: FSMContext):
    _ = call.bot.get('_')

    await call.message.edit_text(_('Приглашение ко вводу года для поиска'),
                                 reply_markup=inline_keyboards.get_cancel_keyboard(_, to='library'))

    await state.update_data(error=False)
    await states.LibraryState.waiting_for_year_input.set()
    await call.answer()


async def start_title_input(call: CallbackQuery, state: FSMContext):
    _ = call.bot.get('_')
    db = call.bot.get('database')

    settings = (await db.settings_worker.select())[0]

    await call.message.edit_text(_('Приглашение ко вводу названия для поиска').format(limit=settings['book_title_limit']),
                                 reply_markup=inline_keyboards.get_cancel_keyboard(_, to='library'))

    await state.update_data(limit=settings['book_title_limit'], error=False)
    await states.LibraryState.waiting_for_title_input.set()
    await call.answer()


async def start_author_input(call: CallbackQuery, state: FSMContext):
    _ = call.bot.get('_')
    db = call.bot.get('database')

    settings = (await db.settings_worker.select())[0]

    await call.message.edit_text(_('Приглашение ко вводу автора для поиска').format(limit=settings['author_limit']),
                                 reply_markup=inline_keyboards.get_cancel_keyboard(_, to='library'))

    await state.update_data(limit=settings['author_limit'], error=False)
    await states.LibraryState.waiting_for_author_input.set()
    await call.answer()


async def genre_choose(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')

    await state.update_data(genre=callback_data['title'], genre_id=callback_data['id'])
    await show_library_menu(call, state)


async def clear_search(call: CallbackQuery, state: FSMContext):
    _ = call.bot.get('_')

    await state.reset_data()
    await show_library_menu(call, state)


async def subscribe_to_search(call: CallbackQuery, state: FSMContext):
    _ = call.bot.get('_')
    db: Database = call.bot.get('database')

    async with state.proxy() as data:
        if not data.get('title') and not data.get('year') and not data.get('author') and not data.get('genre_id'):
            await call.answer(_('Ошибка не выбраны параметры поиска'), show_alert=True)
            return

        await db.archive_worker.add_book_request(data.get('title', ''), data.get('author', ''), data.get('year', 0), call.from_user.id, data.get('genre_id', 'NULL'))

    await call.answer(_('Уведомление о подписке на поисковой запрос'), show_alert=True)


async def get_title(message: Message, state: FSMContext):
    _ = message.bot.get('_')
    redis = message.bot.get('redis')

    main_menu_id = int(await redis.get(name=str(message.from_id)))

    await message.delete()

    async with state.proxy() as data:
        limit = data['limit']
        error = data['error']

    if len(message.text) > limit:
        if not error:
            error_text = _('Ошибка слишком много символов в тексте') + '\n\n'
            await message.bot.edit_message_text(
                chat_id=message.from_id,
                message_id=main_menu_id,
                text=error_text + _('Приглашение ко вводу названия для поиска').format(limit=limit),
                reply_markup=inline_keyboards.get_cancel_keyboard(_, to='library')
            )
            await state.update_data(error=True)
        return

    await state.update_data(title=message.text)
    await message.bot.edit_message_text(
        chat_id=message.from_id,
        message_id=main_menu_id,
        text=_('Уведомление об успешном вводе названия'),
        reply_markup=inline_keyboards.get_back_keyboard(_, to='library')
    )


async def get_author(message: Message, state: FSMContext):
    _ = message.bot.get('_')
    redis = message.bot.get('redis')

    main_menu_id = int(await redis.get(name=str(message.from_id)))

    await message.delete()

    async with state.proxy() as data:
        limit = data['limit']
        error = data['error']

    if len(message.text) > limit:
        if not error:
            error_text = _('Ошибка слишком много символов в тексте') + '\n\n'
            await message.bot.edit_message_text(
                chat_id=message.from_id,
                message_id=main_menu_id,
                text=error_text + _('Приглашение ко вводу автора для поиска').format(limit=limit),
                reply_markup=inline_keyboards.get_cancel_keyboard(_, to='library')
            )
            await state.update_data(error=True)
        return

    await state.update_data(author=message.text)
    await message.bot.edit_message_text(
        chat_id=message.from_id,
        message_id=main_menu_id,
        text=_('Уведомление об успешном вводе автора'),
        reply_markup=inline_keyboards.get_back_keyboard(_, to='library')
    )


async def get_year(message: Message, state: FSMContext):
    _ = message.bot.get('_')
    redis = message.bot.get('redis')

    main_menu_id = int(await redis.get(name=str(message.from_id)))

    await message.delete()

    async with state.proxy() as data:
        error = data['error']

    if not message.text.isdigit():
        if not error:
            error_text = _('Ошибка слишком много символов в тексте') + '\n\n'
            await message.bot.edit_message_text(
                chat_id=message.from_id,
                message_id=main_menu_id,
                text=error_text + _('Приглашение ко вводу года для поиска'),
                reply_markup=inline_keyboards.get_cancel_keyboard(_, to='library')
            )
            await state.update_data(error=True)
        return

    await state.update_data(year=int(message.text))
    await message.bot.edit_message_text(
        chat_id=message.from_id,
        message_id=main_menu_id,
        text=_('Уведомление об успешном вводе года'),
        reply_markup=inline_keyboards.get_back_keyboard(_, to='library')
    )


async def show_genre_choose_menu(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')
    db: Database = call.bot.get('database')
    config: Config = call.bot.get('config')

    async with state.proxy() as data:
        genres = data.get('genres')

    if not genres:
        genres = await db.archive_worker.get_genres()
        await state.update_data(genres=[dict(genre) for genre in genres])

    pages_count = math.ceil(len(genres) / (config.misc.genres_in_row * config.misc.genres_rows_per_page))

    await call.message.edit_text(
        _('Меню выбора хештега для поиска').format(current_page=callback_data['payload'], last_page=pages_count),
        reply_markup=inline_keyboards.get_genres_choose_keyboard(_, genres, config.misc.genres_rows_per_page, config.misc.genres_in_row, int(callback_data['payload']))
    )

    await states.LibraryState.waiting_for_genre_choice.set()
    await call.answer()


async def show_search_result(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')
    db: Database = call.bot.get('database')
    config: Config = call.bot.get('config')

    async with state.proxy() as data:
        genre_id = data.get('genre_id')
        author = data.get('author')
        title = data.get('title')
        year = data.get('year')
        search_result = data.get('search_result')

    if not author and not title and not year and not genre_id:
        await call.answer(_('Ошибка не выбраны параметры поиска'), show_alert=True)
        return

    if not search_result:
        search_result = await db.archive_worker.search(title, author, year, genre_id)
        await state.update_data(search_result=[dict(book) for book in search_result])

    if len(search_result) == 0:
        await call.answer('Ошибка ничего не найдено в архиве', show_alert=True)
        return

    pages_count = math.ceil(len(search_result) / config.misc.search_books_per_page)

    await call.message.edit_text(
        _('Меню выбора книги после поиска').format(current_page=callback_data['payload'], last_page=pages_count),
        reply_markup=inline_keyboards.get_search_books_keyboard(_, search_result, config.misc.search_books_per_page, int(callback_data['payload']))
    )

    await call.answer()


async def show_search_book(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')
    db: Database = call.bot.get('database')

    book = await db.archive_worker.get_book(callback_data['book_id'], call.from_user.id)
    await db.archive_worker.increase_appeal(book['id'])
    text = _('Меню книги из архива').format(
        title=md.escape_md(book['title']),
        author=md.escape_md(book['author']),
        genre=md.escape_md(book['genre']),
        year=book['year'],
        price=md.escape_md(book['price'])
    )
    keyboard = inline_keyboards.get_search_book_menu_keyboard(_, book)

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


async def buy_archive_book(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')
    db: Database = call.bot.get('database')

    user = await db.users_worker.get_user_by_telegram_id(call.from_user.id)

    if int(callback_data['price']) > int(user['balance']):
        await call.answer(_('Ошибка недостаточно баланса'), show_alert=True)
        return

    await db.users_worker.update_balance(call.from_user.id, f'-{callback_data["price"]}')
    await db.archive_worker.add_book_to_purchased(callback_data['book_id'], call.from_user.id)

    await show_search_book(call, callback_data, state)


def register_library(dp: Dispatcher):
    dp.register_callback_query_handler(show_genre_choose_menu, callbacks.library.filter(action='genre'), state=(states.LibraryState.in_menu, states.LibraryState.waiting_for_genre_choice))
    dp.register_callback_query_handler(genre_choose, callbacks.genre_choose.filter(), state=states.LibraryState.waiting_for_genre_choice)
    dp.register_callback_query_handler(clear_search, callbacks.library.filter(action='clear'), state=states.LibraryState.in_menu)
    dp.register_callback_query_handler(start_title_input, callbacks.library.filter(action='title'), state=states.LibraryState.in_menu)
    dp.register_message_handler(get_title, state=states.LibraryState.waiting_for_title_input)
    dp.register_callback_query_handler(start_author_input, callbacks.library.filter(action='author'), state=states.LibraryState.in_menu)
    dp.register_message_handler(get_author, state=states.LibraryState.waiting_for_author_input)
    dp.register_callback_query_handler(start_year_input, callbacks.library.filter(action='year'), state=states.LibraryState.in_menu)
    dp.register_message_handler(get_year, state=states.LibraryState.waiting_for_year_input)
    dp.register_callback_query_handler(show_search_result, callbacks.library.filter(action='search'), state=states.LibraryState.in_menu)
    dp.register_callback_query_handler(subscribe_to_search, callbacks.library.filter(action='subscribe'), state=states.LibraryState.in_menu)
    dp.register_callback_query_handler(show_search_book, callbacks.search_book_choose.filter(), state=states.LibraryState.in_menu)
    dp.register_callback_query_handler(buy_archive_book, callbacks.buy_archive_book.filter(), state=states.LibraryState.in_menu)
