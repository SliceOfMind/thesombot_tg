from aiogram import Dispatcher
from aiogram.types import PollAnswer

from tgbot.services.db.database import Database


async def get_poll_result(poll: PollAnswer):
    db: Database = poll.bot.get('database')

    vote_choices = await db.posts_worker.get_vote_choices(poll.user.id, poll.poll_id)

    await db.posts_worker.update_user_choices(poll.user.id, poll.poll_id, [str(vote_choices[ind]['id']) for ind in poll.option_ids])


def register_polls(dp: Dispatcher):
    dp.register_poll_answer_handler(get_poll_result)
