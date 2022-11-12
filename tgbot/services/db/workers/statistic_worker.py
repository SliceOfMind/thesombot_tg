import asyncpg

from tgbot.services.db.workers.worker_base import Worker
import tgbot.services.db.workers as workers


class StatisticWorker(Worker):
    table_name = 'statistic'

    async def create(self) -> None:
        pass
