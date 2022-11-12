import asyncpg

from tgbot.services.db.workers.worker_base import Worker
import tgbot.services.db.workers as workers


class PostsWorker(Worker):
    table_name = 'post'
    filters_table_name = 'filter'
    post_votes_table_name = 'post_vote'
    vote_choices_table_name = 'vote_choice'
    user_polls_table_name = 'post_userpoll'

    async def create(self) -> None:
        pass

    async def set_is_sent_and_get_posts(self) -> list[asyncpg.Record]:
        sql = f'''
        UPDATE {self.table_name} SET is_sent=TRUE
        WHERE is_sent=FALSE AND send_date < NOW()
        RETURNING *
        '''

        return await self.fetch(sql)

    async def get_filter(self, filter_id) -> asyncpg.Record | None:
        if not filter_id:
            return

        sql = f'SELECT * FROM {self.filters_table_name} WHERE id={filter_id}'

        return await self.fetchone(sql)

    async def get_vote(self, post_id):
        sql = f'''
        SELECT post_vote.id as poll_id, vote_choice.* FROM post_vote, vote_choice
        WHERE post_vote.post_id={post_id} AND vote_choice.post_vote_id=post_vote.id
        '''

        return await self.fetch(sql)

    async def get_vote_choices(self, telegram_id, poll_id) -> list[asyncpg.Record]:
        sql = f'''
        SELECT * FROM {self.vote_choices_table_name} v 
        WHERE 
        v.post_vote_id=(SELECT vote_id 
            FROM {self.user_polls_table_name} 
            WHERE user_id=(SELECT id FROM {workers.UsersWorker.table_name} WHERE telegram_id={telegram_id}) AND poll_id='{poll_id}')
        '''

        return await self.fetch(sql)

    async def update_user_choices(self, telegram_id, poll_id, choices: list) -> None:
        sql = f'''
        UPDATE {self.user_polls_table_name}
        SET choices='{{ {','.join(choices)} }}'
        WHERE user_id=(SELECT id FROM {workers.UsersWorker.table_name} WHERE telegram_id={telegram_id})
        AND poll_id='{poll_id}'
        '''

        await self.execute(sql)

    async def add_user_polls(self, vote_id, user_polls: dict) -> None:
        values_to_insert = list()
        for telegram_id, poll_id in user_polls.items():
            values_to_insert.append(
                f"( (SELECT id FROM {workers.UsersWorker.table_name} WHERE telegram_id={telegram_id}), {vote_id}, '{poll_id}', '{{}}', NOW() )"
            )
        sql = f'''
        INSERT INTO {self.user_polls_table_name} (user_id, vote_id, poll_id, choices, created_at)
        VALUES {', '.join(values_to_insert)}
        '''

        await self.execute(sql)

    async def delete_expired_user_polls(self, duration) -> None:
        sql = f'''
        DELETE FROM {self.user_polls_table_name}
        WHERE id IN (SELECT id FROM {self.user_polls_table_name} WHERE created_at < NOW() - '{duration} days'::interval)
        '''

        await self.execute(sql)
