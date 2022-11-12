import asyncpg

from tgbot.services.db.workers.worker_base import Worker
import tgbot.services.db.workers as workers


class UsersWorker(Worker):
    table_name = 'bot_user'

    async def create(self):
        """
        Table creates by Django ORM

        Fields:


        :return:
        """
        pass

    async def get_user_by_telegram_id(self, telegram_id) -> asyncpg.Record | None:
        sql = f'SELECT * FROM {self.table_name} WHERE telegram_id={telegram_id}'

        return await self.fetchone(sql)

    async def get_user_language_code(self, telegram_id) -> str:
        sql = f'''SELECT language_code FROM {workers.LanguagesWorker.table_name}
              WHERE id=(SELECT language_id FROM {self.table_name} WHERE telegram_id={telegram_id})'''

        return (await self.fetchone(sql))['language_code']

    async def get_telegram_ids(self, users_filter=None) -> list[int]:
        where_clause = list()
        if users_filter:
            if users_filter['balance_from']: where_clause.append(f'balance > {users_filter["balance_from"]}')
            if users_filter['balance_to']: where_clause.append(f'balance < {users_filter["balance_to"]}')
            if users_filter['deposit_from']: where_clause.append(f'deposit > {users_filter["deposit_from"]}')
            if users_filter['deposit_to']: where_clause.append(f'deposit < {users_filter["deposit_to"]}')
            if users_filter['subscribe_time_from']: where_clause.append(f'subscribe_time > {users_filter["subscribe_time_from"]}')
            if users_filter['subscribe_time_to']: where_clause.append(f'subscribe_time < {users_filter["subscribe_time_to"]}')
            if users_filter['language_id']: where_clause.append(f'language_id={users_filter["language_id"]}')
            if users_filter['subscribe_status_id']: where_clause.append(f'subscribe_status_id={users_filter["subscribe_status_id"]}')
            if users_filter['not_end_payment_id'] != 3:
                where_clause.append(f'not_end_payment={bool(users_filter["not_end_payment_id"] - 1)}')

        sql = f'SELECT telegram_id FROM {self.table_name} ' + ' AND '.join(where_clause)

        records = await self.fetch(sql)
        return [record['telegram_id'] for record in records]

    async def add_new_user(self, telegram_id, username, mention, referral_id) -> None:
        if not referral_id:
            referral_id = 'NULL'

        sql = f'''
        INSERT INTO {self.table_name} (telegram_id, username, mention, referral_id, balance, is_block, show_progress,
         deposit, subscribe_time, is_auto_pay, subscribe_status_id, language_id, not_end_payment)
        VALUES ({telegram_id}, '{username}', '{mention}', {referral_id}, 0, false, false, 0, 0, true, 1, 1, false)
        '''

        await self.execute(sql)

    async def is_user_subscriber(self, telegram_id) -> bool:
        sql = f'SELECT subscribe_status_id FROM {self.table_name} WHERE telegram_id={telegram_id}'

        record = await self.fetchone(sql)

        if record['subscribe_status_id'] == 3:
            return True

        return False

    async def update_language(self, telegram_id, lang_code: str) -> None:
        sql = f'''
        UPDATE {self.table_name}
        SET language_id=(SELECT id FROM {workers.LanguagesWorker.table_name} WHERE language_code='{lang_code}')
        WHERE telegram_id={telegram_id}
        '''

        await self.execute(sql)

    async def update_is_block(self, telegram_id, is_block) -> None:
        sql = f'''
        UPDATE {self.table_name}
        SET is_block={is_block}
        WHERE telegram_id={telegram_id}
        '''

        await self.execute(sql)

    async def update_balance(self, telegram_id, update_str: str, user_id=None) -> None:
        """
        :param user_id:
        :param telegram_id:
        :param update_str: '+{value}' - add value | '-{value}' - subtract value | '{value}' - set value
        :return:
        """
        if update_str.startswith('-') or update_str.startswith('+'):
            update_str = f'balance{update_str}'

        sql = f'''
        UPDATE {self.table_name}
        SET balance={update_str}
        WHERE {f'user_id={user_id}' if user_id else f'telegram_id={telegram_id}'}
        '''

        await self.execute(sql)

    async def increase_deposit(self, telegram_id, increase_sum) -> None:
        sql = f'UPDATE {self.table_name} SET deposit=deposit+{increase_sum} WHERE telegram_id={telegram_id}'

        await self.execute(sql)

    async def increase_subscribe_time(self, telegram_id, increase_sum) -> None:
        sql = f'UPDATE {self.table_name} SET subscribe_time=subscribe_time+{increase_sum} WHERE telegram_id={telegram_id}'

        await self.execute(sql)

    async def update_not_end_payment(self, telegram_id, new_value: bool, user_id=None) -> None:
        sql = f'''
        UPDATE {self.table_name}
        SET not_end_payment={new_value}
        WHERE {f'user_id={user_id}' if user_id else f'telegram_id={telegram_id}'}
        '''

        await self.execute(sql)

    async def update_subscribe_status(self, telegram_id, status_id) -> None:
        sql = f'UPDATE {self.table_name} SET subscribe_status_id={status_id} WHERE telegram_id={telegram_id}'

        await self.execute(sql)

    async def update_payment_method(self, telegram_id, payment_method_id) -> None:
        sql = f'''
        UPDATE {self.table_name}
        SET payment_id='{payment_method_id}'
        WHERE telegram_id={telegram_id}
        '''

        await self.execute(sql)

    async def change_show_progress(self, telegram_id) -> bool:
        sql = f'''
        UPDATE {self.table_name} SET
        show_progress=NOT show_progress
        WHERE telegram_id={telegram_id}
        RETURNING show_progress
        '''

        return (await self.fetchone(sql))['show_progress']

    async def change_auto_pay(self, telegram_id) -> bool:
        sql = f'''
        UPDATE {self.table_name} SET
        is_auto_pay=NOT is_auto_pay
        WHERE telegram_id={telegram_id}
        RETURNING is_auto_pay
        '''

        return (await self.fetchone(sql))['is_auto_pay']
