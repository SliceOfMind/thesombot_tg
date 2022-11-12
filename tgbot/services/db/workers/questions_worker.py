import asyncpg

from tgbot.services.db.workers.worker_base import Worker
import tgbot.services.db.workers as workers


class QuestionsWorker(Worker):
    table_name = 'question'

    async def create(self) -> None:
        pass

    async def get_and_set_is_answered_unanswered_questions(self) -> list[asyncpg.Record]:
        sql = f'''
        UPDATE {self.table_name}
        SET is_answered=true
        WHERE is_answered=false AND answer IS NOT NULL
        RETURNING (SELECT telegram_id FROM {workers.UsersWorker.table_name} WHERE {workers.UsersWorker.table_name}.id=from_user_id), answer, text
        '''

        return await self.fetch(sql)

    async def add_question(self, text, telegram_id) -> None:
        sql = f'''
        INSERT INTO {self.table_name} (date, text, is_answered, from_user_id)
        VALUES (NOW(), '{text}', false, (SELECT id FROM {workers.UsersWorker.table_name} WHERE telegram_id={telegram_id}))
        '''

        await self.execute(sql)
