from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery
import aiogram.utils.markdown as md

import tgbot.misc.states as states
import tgbot.keyboards.inline as inline_keyboards
import tgbot.misc.callbacks as callbacks
from tgbot.handlers.main_menu import show_vote_menu
from tgbot.services.db.database import Database
from tgbot.services.custom_broadcasters import MultilingualTextBroadcaster


async def get_question_text(message: Message, state: FSMContext):
    _ = message.bot.get('_')
    redis = message.bot.get('redis')
    db: Database = message.bot.get('database')

    async with state.proxy() as data:
        limit = int(data['limit'])
        error = bool(data['error'])

    main_menu_id = int(await redis.get(name=str(message.from_id)))

    await message.delete()

    question_text = message.text
    if len(question_text) > limit:
        if not error:
            error_text = _('Ошибка слишком много символов в тексте') + '\n\n'
            await message.bot.edit_message_text(
                text=error_text + _('Приглашение ко вводу вопроса').format(limit=limit),
                reply_markup=inline_keyboards.get_cancel_keyboard(_),
                chat_id=message.from_id,
                message_id=main_menu_id
            )
            await state.update_data(error=True)
        return

    await db.questions_worker.add_question(question_text, message.from_id)
    await message.bot.edit_message_text(
        text=_('Уведомление об успешной отправке вопроса'),
        reply_markup=inline_keyboards.get_back_keyboard(_, 'main_menu'),
        chat_id=message.from_id,
        message_id=main_menu_id
    )
    await state.finish()


async def start_offer_book_for_vote(call: CallbackQuery, state: FSMContext):
    _ = call.bot.get('_')
    db: Database = call.bot.get('database')

    settings = (await db.settings_worker.select())[0]

    await state.update_data(limit=settings['book_title_limit'], error=False)

    await call.message.edit_text(_('Приглашение ко вводу названия книги для голосования').format(limit=settings['book_title_limit']),
                                 reply_markup=inline_keyboards.get_cancel_keyboard(_, to='vote'))
    await states.VoteState.waiting_for_input.set()
    await call.answer()


async def get_offer_book(message: Message, state: FSMContext):
    _ = message.bot.get('_')
    redis = message.bot.get('redis')
    db: Database = message.bot.get('database')

    async with state.proxy() as data:
        limit = int(data['limit'])
        error = bool(data['error'])

    main_menu_id = int(await redis.get(name=str(message.from_id)))

    await message.delete()

    if len(message.text) > limit:
        if not error:
            error_text = _('Ошибка слишком много символов в тексте') + '\n\n'
            await message.bot.edit_message_text(
                text=error_text + _('Приглашение ко вводу названия книги для голосования').format(limit=limit),
                reply_markup=inline_keyboards.get_cancel_keyboard(_, to='vote'),
                chat_id=message.from_id,
                message_id=main_menu_id
            )
            await state.update_data(error=True)
        return

    await db.votes_worker.add_book(message.text, message.from_id)
    await message.bot.edit_message_text(
        text=_('Уведомление об успешной отправке книги для голосования'),
        reply_markup=inline_keyboards.get_back_keyboard(_, 'vote'),
        chat_id=message.from_id,
        message_id=main_menu_id
    )
    await state.finish()


async def vote_for_book(call: CallbackQuery, callback_data: dict):
    db: Database = call.bot.get('database')
    _ = call.bot.get('_')
    config = call.bot.get('config')

    if callback_data['action'] == 'add':
        await db.votes_worker.add_user_vote_for_book(call.from_user.id, callback_data['book_id'])
        book = await db.votes_worker.get_book(callback_data['book_id'])
        if int(book['votes_count']) >= int(book['vote_goal']):
            await db.books_worker.add_book(book['title'], book['description'], book['fund_interval'], book['fund_need'],
                                           book['link'], book['price_after_done'], book['price_for_sub'], book['price_common'])
            await db.votes_worker.close_book_vote(book['id'])
            telegram_ids_to_notify = await db.votes_worker.get_telegram_ids_of_voted_users(book['id'])
            _('Уведомление о переходе книги в фандрайзинг')
            await MultilingualTextBroadcaster(
                chats=telegram_ids_to_notify,
                text='Уведомление о переходе книги в фандрайзинг',
                text_kwargs={'title': md.escape_md(book['title'])},
                reply_markup_callback=inline_keyboards.get_close_keyboard,
                bot=call.bot,
                database=db,
                config=config
            ).run()
    else:
        await db.votes_worker.remove_user_vote_for_book(call.from_user.id, callback_data['book_id'])

    await show_vote_menu(call)


def register_questions_and_votes(dp: Dispatcher):
    dp.register_message_handler(get_question_text, state=states.QuestionState.waiting_for_input)
    dp.register_callback_query_handler(start_offer_book_for_vote, callbacks.vote_book.filter(action='offer'))
    dp.register_message_handler(get_offer_book, state=states.VoteState.waiting_for_input)
    dp.register_callback_query_handler(vote_for_book, callbacks.vote_book.filter())
