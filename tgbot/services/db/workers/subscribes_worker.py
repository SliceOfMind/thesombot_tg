import asyncpg

from tgbot.services.db.workers.worker_base import Worker
import tgbot.services.db.workers as workers


class SubscribesWorker(Worker):
    table_name = 'subscribe'
    subscribe_status_table_name = 'subscribe_status'
    subscribes_prices_table_name = 'sub_price'

    async def create(self) -> None:
        pass

    async def get_user_subscribe(self, telegram_id) -> asyncpg.Record | None:
        sql = f'''
        SELECT * FROM {self.table_name} s LEFT JOIN {self.subscribes_prices_table_name} sp on s.sub_price_id = sp.id 
        WHERE user_id=(SELECT id FROM {workers.UsersWorker.table_name} WHERE telegram_id={telegram_id})
        '''

        return await self.fetchone(sql)

    async def get_subscribes_prices(self) -> list[asyncpg.Record]:
        sql = f'SELECT * FROM {self.subscribes_prices_table_name}'

        return await self.fetch(sql)

    async def get_subscribe_price(self, sub_price_id) -> asyncpg.Record:
        sql = f'SELECT * FROM {self.subscribes_prices_table_name} WHERE id={sub_price_id}'

        return await self.fetchone(sql)

    async def get_active_expired_subscribes_with_users(self) -> list[asyncpg.Record]:
        sql = f'''
        SELECT u.id as user_id, s.id as subscribe_id, *
        FROM {workers.UsersWorker.table_name} u LEFT JOIN {self.table_name} s ON u.id = s.user_id
        WHERE NOW() > s.end_date AND u.subscribe_status_id=3
        '''

        return await self.fetch(sql)

    async def is_user_have_active_subscribe(self, user_id) -> bool:
        sql = f'SELECT id FROM {self.table_name} WHERE user_id={user_id} AND is_active=true'

        return bool(await self.fetch(sql))

    async def update_is_active_for_user(self, user_id, is_active):
        sql = f'UPDATE {self.table_name} SET is_active={is_active} WHERE user_id={user_id}'

        await self.execute(sql)

    async def add_user_subscribe(self, user_id, sub_price_id, duration) -> None:
        sql = f'''
        INSERT INTO {self.table_name} (user_id, sub_price_id, is_active, start_date, end_date)
        VALUES ({user_id}, {sub_price_id}, TRUE, NOW(), NOW() + '{duration} months'::interval)
        '''

        await self.execute(sql)

    async def update_user_subscribe(self, user_id, sub_price_id, duration) -> None:
        sql = f'''
        UPDATE {self.table_name} 
        SET sub_price_id={sub_price_id}, start_date=NOW(), end_date=NOW() + '{duration} months'::interval, is_active=TRUE
        WHERE user_id={user_id}
        '''

        await self.execute(sql)

    async def deactivate_user_subscribe(self, user_id) -> None:
        sql = f'UPDATE {self.table_name} SET is_active=FALSE WHERE user_id={user_id}'

        await self.execute(sql)
