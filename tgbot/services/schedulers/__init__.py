import asyncio

import aioschedule
from aiogram import Bot

from tgbot.config import Config
from tgbot.services.schedulers.updates_from_server import get_updates_from_server
from tgbot.services.schedulers.operations_check import check_operations
from tgbot.services.schedulers.subscribes_check import check_subscribes
from tgbot.services.schedulers.other import make_other_actions
from tgbot.services.db.database import Database
from tgbot.services.yoomoney import YooMoney


async def start_schedulers(config: Config, bot: Bot, db: Database, yoomoney: YooMoney):
    aioschedule.every(config.schedulers.updates_from_server_interval).minutes.do(get_updates_from_server, bot, db, config)
    aioschedule.every(config.schedulers.operations_check_interval).minutes.do(check_operations, bot, db, config, yoomoney)
    aioschedule.every(config.schedulers.subscribes_check_interval).minutes.do(check_subscribes, bot, db, config, yoomoney)
    aioschedule.every(config.schedulers.other_interval).minutes.do(make_other_actions, bot, db, config)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)
