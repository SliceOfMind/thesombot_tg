from aiogram import Bot

from tgbot.config import Config, load_config
from tgbot.services.db.database import Database


async def make_other_actions(bot: Bot, db: Database, config: Config):
    await delete_users_polls(db)
    await reload_i18n(bot)
    await reload_config(bot)


async def delete_users_polls(db: Database):
    await db.posts_worker.delete_expired_user_polls(7)


async def reload_i18n(bot: Bot):
    i18n = bot.get('_')
    i18n.reload()
    bot['_'] = i18n


async def reload_config(bot: Bot):
    config = load_config('.env')
    bot['config'] = config
