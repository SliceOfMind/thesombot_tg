import asyncpg

from tgbot.services.db.workers.worker_base import Worker


class SettingsWorker(Worker):
    table_name = 'settings'

    async def create(self) -> None:
        pass
