from aiogram import Bot
from aiogram.utils.exceptions import BotBlocked

from tgbot.config import Config
from tgbot.services.db.database import Database
from tgbot.services.custom_broadcasters import MultilingualTextBroadcaster, PollBroadcaster, FileBroadcaster, LanguageContext
import tgbot.keyboards.inline as inline_keyboards


async def get_updates_from_server(bot: Bot, db: Database, config: Config):
    await send_fundraising_books_available_notification(bot, db, config)
    await send_questions_answers(bot, db, config)
    await send_posts(bot, db, config)


async def send_fundraising_books_available_notification(bot: Bot, db: Database, config: Config):
    books_to_notify = await db.books_worker.get_and_update_available_books_to_notify()

    for book in books_to_notify:
        telegram_ids_of_users_to_notify = await db.books_worker.get_telegram_ids_of_users_who_purchased_book(book['id'])

        await MultilingualTextBroadcaster(
            chats=telegram_ids_of_users_to_notify,
            text='Уведомление о доступности книги из фандрайзинга',
            text_kwargs={'title': book['name']},
            reply_markup_callback=inline_keyboards.get_close_keyboard,
            bot=bot,
            database=db,
            config=config
        ).run()


async def send_questions_answers(bot: Bot, db: Database, config: Config):
    questions = await db.questions_worker.get_and_set_is_answered_unanswered_questions()

    for question in questions:
        async with LanguageContext(question['telegram_id'], db, config) as _:
            try:
                await bot.send_message(
                    chat_id=question['telegram_id'],
                    text=_('Уведомление об ответе на вопрос').format(text=question['text'], answer=question['answer']),
                    reply_markup=inline_keyboards.get_close_keyboard(_)
                )
            except BotBlocked:
                await db.users_worker.update_is_block(question['telegram_id'], True)


async def send_posts(bot: Bot, db: Database, config: Config):
    posts = await db.posts_worker.set_is_sent_and_get_posts()

    for post in posts:
        users_filter = await db.posts_worker.get_filter(post['filter_id'])
        telegram_ids_to_notify = await db.users_worker.get_telegram_ids(users_filter)

        if post['vote_options']:
            poll = await db.posts_worker.get_vote(post['id'])
            broadcaster = PollBroadcaster(
                chats=telegram_ids_to_notify,
                question=post['title'] + '\n\n' + post['text'],
                options=[el['choice_text'] for el in poll],
                is_anonymous=False,
                allows_multiple_answers=True,
                reply_markup_callback=inline_keyboards.get_post_keyboard,
                reply_kwargs={'link': post['link']},
                bot=bot,
                database=db,
                config=config
            )
            await broadcaster.run()
            await db.posts_worker.add_user_polls(poll[0]['poll_id'], broadcaster.poll_ids)

        elif post['photo']:
            await FileBroadcaster(
                chats=telegram_ids_to_notify,
                file_path=config.misc.web_base_dir + post['photo'],
                caption=post['title'] + '\n\n' + post['text'],
                reply_markup_callback=inline_keyboards.get_post_keyboard,
                reply_kwargs={'link': post['link']},
                bot=bot,
                database=db,
                config=config
            ).run()

        else:
            await MultilingualTextBroadcaster(
                chats=telegram_ids_to_notify,
                text=post['title'] + '\n\n' + post['text'],
                reply_markup_callback=inline_keyboards.get_post_keyboard,
                reply_kwargs={'link': post['link']},
                bot=bot,
                database=db,
                config=config
            ).run()
