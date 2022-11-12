import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aioredis import Redis

from tgbot.config import load_config
from tgbot.filters.admin import AdminFilter
from tgbot import handlers
from tgbot import middlewares
from tgbot.services.db.database import Database
from tgbot.services.schedulers import start_schedulers
from tgbot.services.yoomoney import YooMoney

logger = logging.getLogger(__name__)


def register_all_middlewares(dp, config):
    dp.setup_middleware(middlewares.EnvironmentMiddleware(config=config))
    dp.setup_middleware(middlewares.ThrottlingMiddleware())
    if config.telegram_bot.extended_logs: dp.setup_middleware(LoggingMiddleware())

    i18n = middlewares.ACLMiddleware(config.misc.i18n_domain, config.misc.locales_dir)
    dp.bot['_'] = i18n
    dp.setup_middleware(i18n)


def register_all_filters(dp):
    dp.filters_factory.bind(AdminFilter)


def register_all_handlers(dp):
    handlers.register_main_menu(dp)
    handlers.register_other(dp)
    handlers.register_fundraising(dp)
    handlers.register_commands(dp)
    handlers.register_language(dp)
    handlers.register_errors(dp)
    handlers.register_questions_and_votes(dp)
    handlers.register_subscribes(dp)
    handlers.register_balance_top_up(dp)
    handlers.register_library(dp)
    handlers.register_polls(dp)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
        handlers=(logging.FileHandler(r'logs.log'), logging.StreamHandler())
    )
    logger.info('Starting bot')
    config = load_config('.env')

    storage = RedisStorage2() if config.telegram_bot.use_redis else MemoryStorage()
    bot = Bot(token=config.telegram_bot.token, parse_mode='MarkdownV2')
    dispatcher = Dispatcher(bot, storage=storage)

    database = Database(
        host=config.database.host,
        password=config.database.password,
        user=config.database.user,
        database=config.database.database,
        port=config.database.port
    )

    redis = Redis()

    yoomoney = YooMoney(config)

    bot['config'] = config
    bot['database'] = database
    bot['redis'] = redis
    bot['yoomoney'] = yoomoney

    register_all_middlewares(dispatcher, config)
    register_all_filters(dispatcher)
    register_all_handlers(dispatcher)

    asyncio.create_task(start_schedulers(config, bot, database, yoomoney))

    try:
        await dispatcher.start_polling()
    finally:
        await database.close_pools()
        await redis.save()

        await dispatcher.storage.close()
        await dispatcher.storage.wait_closed()

        session = await bot.get_session()
        await session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit) as e:
        logger.info('Bot stopped!')
        raise e
