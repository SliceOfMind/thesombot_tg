import asyncpg

from tgbot.services.db.workers.worker_base import Worker
import tgbot.services.db.workers as workers


class VotesWorker(Worker):
    table_name = 'vote_book'
    user_votes_table_name = 'user_book_vote'

    async def create(self) -> None:
        pass

    async def get_book(self, book_id) -> asyncpg.Record:
        sql = f'''
        SELECT *, (SELECT COUNT(*) FROM user_book_vote WHERE book_id={book_id}) as votes_count FROM {self.table_name}
        WHERE id={book_id}
        '''

        return await self.fetchone(sql)

    async def get_books_for_vote_for_user(self, telegram_id) -> list[asyncpg.Record]:
        sql = f'''
        SELECT *, (SELECT COUNT(*) FROM {self.user_votes_table_name} WHERE book_id={self.table_name}.id) as votes_count,
        (SELECT id FROM {self.user_votes_table_name}
         WHERE book_id={self.table_name}.id 
         AND user_id=(SELECT id FROM {workers.UsersWorker.table_name} WHERE telegram_id={telegram_id}))
         IS NOT NULL as is_voted_by_user
        FROM {self.table_name}
        WHERE is_visible=TRUE AND is_fund_sent=FALSE
        ORDER BY title
        '''

        return await self.fetch(sql)

    async def get_telegram_ids_of_voted_users(self, book_id) -> list[int]:
        sql = f'''
        SELECT telegram_id 
        FROM {workers.UsersWorker.table_name} 
        WHERE id=(SELECT user_id FROM {self.user_votes_table_name} WHERE {workers.UsersWorker.table_name}.id=user_id AND book_id={book_id})
        '''

        records = await self.fetch(sql)
        return [record['telegram_id'] for record in records]

    async def add_user_vote_for_book(self, telegram_id, book_id) -> None:
        sql = f'''
        INSERT INTO {self.user_votes_table_name} (user_id, book_id, created_at)
        VALUES ((SELECT id FROM {workers.UsersWorker.table_name} WHERE telegram_id={telegram_id}), {book_id}, NOW())
        '''

        await self.execute(sql)

    async def remove_user_vote_for_book(self, telegram_id, book_id) -> None:
        sql = f'''
        DELETE FROM {self.user_votes_table_name}
        WHERE user_id=(SELECT id FROM {workers.UsersWorker.table_name} WHERE telegram_id={telegram_id}) AND book_id={book_id}
        '''

        await self.execute(sql)

    async def add_book(self, title, telegram_id) -> None:
        sql = f'''
        INSERT INTO {self.table_name} (title, user_id, created_at, is_visible, vote_goal, fund_interval, fund_need, is_fund_sent, description, link, price_after_done, price_common, price_for_sub)
        VALUES ('{title}', (SELECT id FROM {workers.UsersWorker.table_name} WHERE telegram_id={telegram_id}), NOW(), FALSE, 0, 0, 0, FALSE, '', '', 0, 0, 0)
        '''

        await self.execute(sql)

    async def close_book_vote(self, book_id) -> None:
        sql = f'''
        UPDATE {self.table_name}
        SET is_visible=FALSE, is_fund_sent=TRUE
        WHERE id={book_id}
        '''

        await self.execute(sql)
