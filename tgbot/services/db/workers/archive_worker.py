import asyncpg

from tgbot.services.db.workers.worker_base import Worker
import tgbot.services.db.workers as workers


class ArchiveWorker(Worker):
    table_name = 'book_archive'
    genres_table_name = 'genre'
    authors_table_name = 'author'
    requests_table_name = 'book_request'
    purchased_books_table_name = 'purchased_archive_book'

    async def create(self) -> None:
        pass

    async def get_book(self, book_id, telegram_id) -> asyncpg.Record:
        sql = f'''
        SELECT 
            *, 
            (SELECT id FROM {self.purchased_books_table_name} WHERE book_id={book_id} AND user_id=(SELECT id FROM {workers.UsersWorker.table_name} WHERE telegram_id={telegram_id})) AS is_purchased,
            (SELECT title FROM {self.authors_table_name} WHERE id=author_id) as author,
            (SELECT title FROM {self.genres_table_name} WHERE id=genre_id) as genre
        FROM {self.table_name}
        WHERE id={book_id}   
        '''

        return await self.fetchone(sql)

    async def search(self, title, author, year, genre_id) -> list[asyncpg.Record]:
        where_clause = []
        if title: where_clause.append(f"SIMILARITY(title, '{title}') >= 0.3")
        if author: where_clause.append(f"author_id IN (SELECT id FROM {self.authors_table_name} WHERE SIMILARITY(title, '{author}') >= 0.3)")
        if year:
            if title or author or genre_id:
                where_clause.append(f"(year='{year}' OR (year IS NULL))")
            else:
                where_clause.append(f"year='{year}'")
        if genre_id: where_clause.append(f'genre_id={genre_id}')

        sql = f'''
        SELECT id, title FROM {self.table_name}
        WHERE {' AND '.join(where_clause)}
        '''

        return await self.fetch(sql)

    async def get_genres(self) -> list[asyncpg.Record]:
        sql = f'SELECT * FROM {self.genres_table_name} ORDER BY id'

        return await self.fetch(sql)

    async def increase_appeal(self, book_id):
        sql = f'UPDATE {self.table_name} SET appeal=appeal+1 WHERE id={book_id}'

        await self.execute(sql)

    async def add_book_request(self, title, author, year, telegram_id, genre_id) -> None:
        sql = f'''
        INSERT INTO {self.requests_table_name} (title, author, year, is_approved, user_id, genre_id, created_at)
        VALUES ('{title}', '{author}', '{year}', false, (SELECT id FROM {workers.UsersWorker.table_name} WHERE telegram_id={telegram_id}), {genre_id}, NOW())
        '''

        await self.execute(sql)

    async def add_book_to_purchased(self, book_id, telegram_id) -> None:
        sql = f'''
        INSERT INTO {self.purchased_books_table_name} (book_id, user_id)
        VALUES ({book_id}, (SELECT id FROM {workers.UsersWorker.table_name} WHERE telegram_id={telegram_id}))
        '''

        await self.execute(sql)
