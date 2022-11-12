import asyncpg

from tgbot.services.db.workers.worker_base import Worker
import tgbot.services.db.workers as workers


class BooksWorker(Worker):
    table_name = 'book'
    users_books_table_name = 'book_user'

    async def create(self) -> None:
        pass

    async def get_active_books(self) -> list[asyncpg.Record]:
        sql = f'''
        SELECT * FROM {self.table_name}
        WHERE NOW() BETWEEN start_date AND end_date
        '''

        return await self.fetch(sql)

    async def get_telegram_ids_of_users_who_purchased_book(self, book_id) -> list[int]:
        sql = f'''
        SELECT telegram_id FROM {workers.UsersWorker.table_name}, {self.users_books_table_name}
        WHERE book_id={book_id} AND user_id={workers.UsersWorker.table_name}.id
        '''

        records = await self.fetch(sql)

        return [record['telegram_id'] for record in records]

    async def get_and_update_available_books_to_notify(self) -> list[asyncpg.Record]:
        sql = f'''
        UPDATE {self.table_name}
        SET is_notification_sent=TRUE
        WHERE is_available=TRUE AND is_notification_sent=FALSE
        RETURNING *
        '''

        return await self.fetch(sql)

    async def is_user_purchased_book(self, user_id, book_id) -> bool:
        sql = f'SELECT id FROM {self.users_books_table_name} WHERE book_id={book_id} AND user_id={user_id}'

        record = await self.fetchone(sql)
        return bool(record)

    async def add_purchased_book(self, user_id, book_id) -> None:
        sql = f'INSERT INTO {self.users_books_table_name} (user_id, book_id) VALUES ({user_id}, {book_id})'

        await self.execute(sql)

    async def add_book(self, title, description, interval, goal_sum, link, price_after_done, price_for_sub, price_common):
        sql = f'''
        INSERT INTO {self.table_name} (name, description, start_date, end_date, goal_sum, collected_sum, link, is_done,
        price_after_done, price_for_sub, price_common, is_available, is_notification_sent)
        VALUES ('{title}', '{description}', NOW(), NOW() + '{interval} days'::interval, {goal_sum}, 0, '{link}', FALSE,
        {price_after_done}, {price_for_sub}, {price_common}, FALSE, FALSE) 
        '''

        await self.execute(sql)

    async def increase_collected_sum(self, book_id, add_value) -> None:
        sql = f'UPDATE {self.table_name} SET collected_sum=collected_sum+{add_value} WHERE id={book_id}'

        await self.execute(sql)

    async def update_is_done(self, book_id, value) -> None:
        sql = f'UPDATE {self.table_name} SET is_done={value} WHERE id={book_id}'

        await self.execute(sql)
