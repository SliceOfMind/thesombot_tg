import asyncpg

from tgbot.services.db.workers.worker_base import Worker


class LanguagesWorker(Worker):
    table_name = 'language'

    async def create(self) -> None:
        pass
