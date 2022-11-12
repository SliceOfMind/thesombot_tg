import math

import asyncpg
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButtonPollType

import tgbot.misc.callbacks as callbacks
from tgbot.misc.other import strike_text


def get_choose_language_keyboard(languages: list[tuple]) -> InlineKeyboardMarkup:
    """
    :param languages: List of tuple with languages from database (first - language code, second - Text for button)
    :return: keyboard
    """
    keyboard = InlineKeyboardMarkup()

    for lang_code, lang_name in languages:
        keyboard.add(InlineKeyboardButton(lang_name, callback_data=callbacks.languages.new(code=lang_code)))

    return keyboard


def get_main_menu_keyboard(_, locale=None) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Описание бота"', locale=locale), url=_('Ссылка на описание бота', locale=locale))
    )

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Подписки"', locale=locale), callback_data=callbacks.navigation.new(to='subscribes', payload='')),
        InlineKeyboardButton(_('Кнопка "Информация"', locale=locale), callback_data=callbacks.navigation.new(to='information', payload=''))
    )

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Фандрайзинг"', locale=locale), callback_data=callbacks.navigation.new(to='fundraising', payload='')),
        InlineKeyboardButton(_('Кнопка "Архив книг"', locale=locale), callback_data=callbacks.navigation.new(to='library', payload=''))
    )

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Задать вопрос"', locale=locale), callback_data=callbacks.navigation.new(to='ask_question', payload='')),
        InlineKeyboardButton(_('Кнопка "Баланс"', locale=locale), callback_data=callbacks.navigation.new(to='balance', payload=''))
    )

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Проголосовать за книгу"', locale=locale), callback_data=callbacks.navigation.new(to='vote', payload=''))
    )

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Изменить язык"', locale=locale), callback_data=callbacks.navigation.new(to='language_choose', payload=''))
    )

    return keyboard


def get_back_keyboard(_, to: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Назад"'), callback_data=callbacks.navigation.new(to=to, payload=''))
    )

    return keyboard


def get_information_keyboard(_) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Пользовательское соглашение"'), url=_('Ссылка на пользовательское соглашение'))
    )

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Назад"'), callback_data=callbacks.navigation.new(to='main_menu', payload=''))
    )

    return keyboard


def get_balance_keyboard(_, book_id=None) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Пополнить баланс"'), callback_data='top_up')
    )

    if book_id:
        keyboard.add(
            InlineKeyboardButton(_('Кнопка "Назад"'), callback_data=callbacks.fundraising_book.new(book_id=book_id))
        )
    else:
        keyboard.add(
            InlineKeyboardButton(_('Кнопка "Назад"'), callback_data=callbacks.navigation.new(to='main_menu', payload=''))
        )

    return keyboard


def get_subscribes_keyboard(_, subscribes, promo_code, user) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Анонс на ближайший месяц"'), url=_('Ссылка на анонс на ближайший месяц'))
    )

    if user['subscribe_status_id'] != 3:
        for subscribe in subscribes:
            if promo_code and subscribe['id'] in promo_code['subscribes_ids']:
                price = round(subscribe['value'] * ((100 - promo_code['discount']) / 100))
                if price == 0: price += 1
                price_str = f'( {strike_text(subscribe["value"])} ) {price}'
            else:
                price = price_str = subscribe['value']

            keyboard.add(
                InlineKeyboardButton(_('Кнопка с подпиской').format(duration=subscribe['duration'], price=price_str),
                                     callback_data=callbacks.payment_method_choose.new(method='bank_card', action='sub', amount=price, payload=subscribe['id']))
            )
    else:
        keyboard.add(
            InlineKeyboardButton(_('Кнопка "Вкл/выкл автоплатёж"'), callback_data='change_auto_pay')
        )

    if promo_code:
        keyboard.add(
            InlineKeyboardButton(_('Кнопка "Отменить промокод"'),
                                 callback_data=callbacks.promo_code.new(action='cancel'))
        )
    else:
        keyboard.add(
            InlineKeyboardButton(_('Кнопка "Ввести промокод"'), callback_data=callbacks.promo_code.new(action='use'))
        )

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Назад"'), callback_data=callbacks.navigation.new(to='main_menu', payload=''))
    )

    return keyboard


def get_fundraising_keyboard(_, books: list[asyncpg.Record]) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    for book in books:
        keyboard.add(
            InlineKeyboardButton(book['name'], callback_data=callbacks.fundraising_book.new(book_id=book['id']))
        )

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Назад"'), callback_data=callbacks.navigation.new(to='main_menu', payload=''))
    )

    return keyboard


def get_fundraising_book_keyboard(_, is_purchased, is_user_subscriber, book, price) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    if is_purchased:
        if book['is_available']:
            keyboard.add(
                InlineKeyboardButton(_('Кнопка "Скачать"'), url=book['link'])
            )
        else:
            keyboard.add(
                InlineKeyboardButton(_('Кнопка "Скачать"'), callback_data='book_isnt_available')
            )
    else:
        keyboard.add(
            InlineKeyboardButton(_('Кнопка "Оплатить"'), callback_data=callbacks.buy_fundraising_book.new(book_id=book['id'], price=price))
        )

    if is_user_subscriber:
        keyboard.add(
            InlineKeyboardButton(_('Кнопка "Вкл/выкл прогресс"'), callback_data=callbacks.change_show_progress.new(book_id=book['id']))
        )

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Назад"'), callback_data=callbacks.navigation.new(to='fundraising', payload=''))
    )

    return keyboard


def get_close_keyboard(_, is_final=True) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Закрыть"'), callback_data=callbacks.close.new(is_final=is_final))
    )

    return keyboard


def get_cancel_keyboard(_, to='main_menu') -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Отмена"'), callback_data=callbacks.cancel.new(to=to))
    )

    return keyboard


def get_votes_menu_keyboard(_, books) -> InlineKeyboardMarkup():
    keyboard = InlineKeyboardMarkup()

    for book in books:
        is_voted = '✅' if book['is_voted_by_user'] else '❌'
        keyboard.add(
            InlineKeyboardButton(_('Кнопка для голосования за книгу').format(title=book['title'], is_voted=is_voted),
                                 callback_data=callbacks.vote_book.new(action='remove' if book['is_voted_by_user'] else 'add', book_id=book['id']))
        )

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Предложить книгу"'), callback_data=callbacks.vote_book.new(action='offer', book_id=''))
    )

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Назад"'), callback_data=callbacks.navigation.new(to='main_menu', payload=''))
    )

    return keyboard


def get_library_menu_keyboard(_) -> InlineKeyboardMarkup():
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Хештеги"'), url=_('Ссылка на хештеги'))
    )

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Поиск по названию"'), callback_data=callbacks.library.new('title', '')),
        InlineKeyboardButton(_('Кнопка "Поиск по хештегу"'), callback_data=callbacks.library.new('genre', 1))
    )

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Поиск по году"'), callback_data=callbacks.library.new('year', '')),
        InlineKeyboardButton(_('Кнопка "Поиск по автору"'), callback_data=callbacks.library.new('author', ''))
    )

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Подписаться на запрос"'), callback_data=callbacks.library.new('subscribe', ''))
    )

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Искать"'), callback_data=callbacks.library.new('search', 1)),
        InlineKeyboardButton(_('Кнопка "Очистить"'), callback_data=callbacks.library.new('clear', ''))
    )

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Назад"'), callback_data=callbacks.navigation.new(to='main_menu', payload=''))
    )

    return keyboard


def get_genres_choose_keyboard(_, genres, rows_per_page, genres_per_row, page) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    genres_per_page = rows_per_page * genres_per_row
    genres_to_display = genres[(page - 1) * genres_per_page:page * genres_per_page]
    for row in range(rows_per_page):
        row_genres = [genre for genre in genres_to_display[row * genres_per_row:(row + 1) * genres_per_row]]

        keyboard.row(
            *[InlineKeyboardButton(genre['number'],
                                   callback_data=callbacks.genre_choose.new(genre['title'], genre['id'])) for genre in row_genres]
        )

    pages_count = math.ceil(len(genres) / genres_per_page)
    if pages_count > 1:
        next_button = InlineKeyboardButton('>>>', callback_data=callbacks.library.new('genre', page + 1))
        prev_button = InlineKeyboardButton('<<<', callback_data=callbacks.library.new('genre', page - 1))

        if page == 1:
            keyboard.add(next_button)
        elif page == pages_count:
            keyboard.add(prev_button)
        else:
            keyboard.add(prev_button, next_button)

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Назад"'), callback_data=callbacks.navigation.new(to='library', payload=''))
    )

    return keyboard


def get_search_books_keyboard(_, books, books_per_page, page) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    books_to_display = books[(page - 1) * books_per_page:page * books_per_page]
    for book in books_to_display:
        keyboard.add(
            InlineKeyboardButton(book['title'], callback_data=callbacks.search_book_choose.new(book_id=book['id']))
        )

    pages_count = math.ceil(len(books) / books_per_page)
    if pages_count > 1:
        next_button = InlineKeyboardButton('>>>', callback_data=callbacks.library.new('search', page + 1))
        prev_button = InlineKeyboardButton('<<<', callback_data=callbacks.library.new('search', page - 1))

        if page == 1:
            keyboard.add(next_button)
        elif page == pages_count:
            keyboard.add(prev_button)
        else:
            keyboard.add(prev_button, next_button)

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Назад"'), callback_data=callbacks.navigation.new(to='library', payload=''))
    )

    return keyboard


def get_choose_payment_method_keyboard(_, action, amount, payload='') -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "ЮKassa"'),
                             callback_data=callbacks.payment_method_choose.new(method='yookassa', action=action, amount=amount, payload=payload))
    )

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Назад"'), callback_data=callbacks.navigation.new(to='balance', payload=''))
    )

    return keyboard


def get_pay_keyboard(_, pay_url, to) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Оплатить"'), url=pay_url)
    )

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Назад"'), callback_data=callbacks.navigation.new(to=to, payload=''))
    )

    return keyboard


def get_search_book_menu_keyboard(_, book) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    if not book['is_purchased']:
        keyboard.add(
            InlineKeyboardButton(_('Кнопка "Оплатить"'),
                                 callback_data=callbacks.buy_archive_book.new(book['id'], book['price']))
        )
    else:
        if book['link']:
            keyboard.add(
                InlineKeyboardButton(_('Кнопка "Скачать"'), url=book['link'])
            )
        else:
            keyboard.add(
                InlineKeyboardButton(_('Кнопка "Скачать"'), callback_data='book_isnt_available')
            )

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Назад"'), callback_data=callbacks.library.new('search', 1))
    )

    return keyboard


def get_post_keyboard(_, link=None) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    if link:
        keyboard.add(
            InlineKeyboardButton(_('Кнопка "Подробнее"'), url=link)
        )

    keyboard.add(
        InlineKeyboardButton(_('Кнопка "Закрыть"'), callback_data=callbacks.close.new(is_final=''))
    )

    return keyboard

