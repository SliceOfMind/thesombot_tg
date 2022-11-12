import asyncpg

from tgbot.services.db.workers.worker_base import Worker
import tgbot.services.db.workers as workers


class OperationsWorker(Worker):
    table_name = 'operation'

    async def create(self) -> None:
        pass

    async def get_operations_with_telegram_ids(self, type) -> list[asyncpg.Record] | None:
        sql = f'''
        SELECT *, (SELECT telegram_id FROM {workers.UsersWorker.table_name} WHERE id=user_id) as telegram_id
        FROM {self.table_name} WHERE type='{type}'
        '''

        return await self.fetch(sql)

    async def add_operation(self, telegram_id, payment_id, amount, type, payload='') -> None:
        sql = f'''
        INSERT INTO {self.table_name} (user_id, payment_id, top_up, type, payload)
        VALUES ((SELECT id FROM {workers.UsersWorker.table_name} WHERE telegram_id={telegram_id}), '{payment_id}', {amount}, '{type}', '{payload}')
        '''

        await self.execute(sql)

    async def delete_operation(self, operation_id) -> None:
        sql = f'''
        DELETE FROM {self.table_name}
        WHERE id={operation_id}
        '''

        await self.execute(sql)
