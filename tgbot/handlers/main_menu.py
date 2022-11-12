from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery
import aiogram.utils.markdown as md

from tgbot.services.db.database import Database
import tgbot.keyboards.inline as inline_keyboards
import tgbot.misc.callbacks as callbacks
import tgbot.misc.states as states


async def show_main_menu(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')
    locale = callback_data.get('locale')

    await call.message.edit_text(_('Главное меню', locale=locale),
                                 reply_markup=inline_keyboards.get_main_menu_keyboard(_, locale=locale))
    await state.finish()
    await call.answer()


async def show_choose_language(call: CallbackQuery):
    db: Database = call.bot.get('database')
    _ = call.bot.get('_')

    languages = await db.languages_worker.select()
    languages = [(lang['language_code'], lang['name']) for lang in languages]

    await call.message.edit_text(_('Выбор языка'),
                                 reply_markup=inline_keyboards.get_choose_language_keyboard(languages))
    await call.answer()


async def show_information(call: CallbackQuery):
    _ = call.bot.get('_')

    await call.message.edit_text(_('Информация'), reply_markup=inline_keyboards.get_information_keyboard(_))
    await call.answer()


def get_subscribe_status(_, user_subscribe, promo_code) -> str:
    if not user_subscribe:
        return _('Отсутствие подписки')
    if user_subscribe['is_active']:
        price = user_subscribe['value']
        if promo_code and user_subscribe['sub_price_id'] in promo_code['subscribes_ids']:
            price = round(user_subscribe['value'] * ((100 - promo_code['discount']) / 100))
            if price == 0: price += 1

        return _('Активная подписка').format(end_date=md.escape_md(user_subscribe['end_date']), price=price)

    return _('Просроченная подписка').format(end_date=md.escape_md(user_subscribe['end_date']))


async def show_balance(call: CallbackQuery, callback_data: dict):
    _ = call.bot.get('_')
    db: Database = call.bot.get('database')
    book_id = callback_data['payload']

    user = await db.users_worker.get_user_by_telegram_id(call.from_user.id)

    promo_code = await db.promo_codes_worker.get_user_promo_code(user['id'])
    if promo_code:
        promo_code = await db.promo_codes_worker.get_promo_code(promo_code['promo_code'])
    subscribe_status = get_subscribe_status(_, await db.subscribes_worker.get_user_subscribe(call.from_user.id), promo_code)
    await call.message.edit_text(_('Меню баланса').format(balance=user['balance'], subscribe=subscribe_status),
                                 reply_markup=inline_keyboards.get_balance_keyboard(_, book_id))
    await call.answer()


async def show_subscribes_menu(call: CallbackQuery):
    _ = call.bot.get('_')
    db: Database = call.bot.get('database')

    user = await db.users_worker.get_user_by_telegram_id(call.from_user.id)
    promo_code = await db.promo_codes_worker.get_user_promo_code(user['id'])
    subscribes = await db.subscribes_worker.get_subscribes_prices()

    if promo_code:
        promo_code = await db.promo_codes_worker.get_promo_code(promo_code['promo_code'])
    subscribe_status = get_subscribe_status(_, await db.subscribes_worker.get_user_subscribe(call.from_user.id), promo_code)
    if user['is_auto_pay']:
        auto_pay_status = _('Автоплатёж включён')
    else:
        auto_pay_status = _('Автоплатёж выключен')

    await call.message.edit_text(
        _('Меню подписок').format(subscribe=subscribe_status, auto_pay=auto_pay_status),
        reply_markup=inline_keyboards.get_subscribes_keyboard(_, subscribes, promo_code, user)
    )
    await call.answer()


async def show_fundraising_menu(call: CallbackQuery):
    _ = call.bot.get('_')
    db: Database = call.bot.get('database')

    books = await db.books_worker.get_active_books()

    await call.message.edit_text(_('Меню фандрайзинга'),
                                 reply_markup=inline_keyboards.get_fundraising_keyboard(_, books))
    await call.answer()


async def show_library_menu(call: CallbackQuery, state: FSMContext):
    _ = call.bot.get('_')

    async with state.proxy() as data:
        genre = data.get('genre')
        author = data.get('author')
        title = data.get('title')
        year = data.get('year')

        data['genres'] = ''
        data['search_result'] = ''

    text = _('Меню архива книг').format(
        genre=md.escape_md(genre if genre else '❌'),
        year=year if year else '❌',
        author=md.escape_md(author if author else '❌'),
        title=md.escape_md(title if title else '❌')
    )
    await call.message.edit_text(text, reply_markup=inline_keyboards.get_library_menu_keyboard(_))
    await states.LibraryState.in_menu.set()
    await call.answer()


async def start_question_input(call: CallbackQuery, state: FSMContext):
    _ = call.bot.get('_')
    db = call.bot.get('database')

    settings = (await db.settings_worker.select())[0]

    await call.message.edit_text(_('Приглашение ко вводу вопроса').format(limit=settings['question_symbols_limit']),
                                 reply_markup=inline_keyboards.get_cancel_keyboard(_))

    await state.update_data(error=False, limit=settings['question_symbols_limit'])
    await states.QuestionState.waiting_for_input.set()
    await call.answer()


async def show_vote_menu(call: CallbackQuery):
    _ = call.bot.get('_')
    db: Database = call.bot.get('database')

    books = await db.votes_worker.get_books_for_vote_for_user(call.from_user.id)

    books_text = ''
    for book in books:
        books_text += _('Формат книги в меню голосования').format(title=md.escape_md(book['title']), count=book['votes_count']) + '\n'
    votes_menu_text = _('Меню голосования за книгу').format(books=books_text)

    await call.message.edit_text(votes_menu_text, reply_markup=inline_keyboards.get_votes_menu_keyboard(_, books))
    await call.answer()


def register_main_menu(dp: Dispatcher):
    dp.register_callback_query_handler(show_main_menu, callbacks.navigation.filter(to='main_menu'), state='*')
    dp.register_callback_query_handler(show_balance, callbacks.navigation.filter(to='balance'))
    dp.register_callback_query_handler(show_information, callbacks.navigation.filter(to='information'))
    dp.register_callback_query_handler(show_choose_language, callbacks.navigation.filter(to='language_choose'))
    dp.register_callback_query_handler(show_subscribes_menu, callbacks.navigation.filter(to='subscribes'))
    dp.register_callback_query_handler(show_fundraising_menu, callbacks.navigation.filter(to='fundraising'))
    dp.register_callback_query_handler(show_library_menu, callbacks.navigation.filter(to='library'), state='*')
    dp.register_callback_query_handler(start_question_input, callbacks.navigation.filter(to='ask_question'))
    dp.register_callback_query_handler(show_vote_menu, callbacks.navigation.filter(to='vote'))
