import asyncpg

from tgbot.services.db.workers.worker_base import Worker
import tgbot.services.db.workers as workers


class PromoCodesWorker(Worker):
    table_name = 'promo_code'
    promo_code_subscribes_prices_table_name = 'promo_code_sub_price_id'
    promo_code_users = 'promo_code_user'

    async def create(self) -> None:
        pass

    async def get_user_promo_code(self, user_id=None, telegram_id=None) -> asyncpg.Record | None:
        if telegram_id:
            user_id = f'(SELECT id FROM {workers.UsersWorker.table_name} WHERE telegram_id={telegram_id})'

        sql = f'''
        SELECT 
            * 
        FROM 
            promo_code p, promo_code_user pu 
        WHERE 
            pu.user_id={user_id} AND p.id=pu.promo_code_id AND pu.active='1'
        '''

        return await self.fetchone(sql)

    async def get_promo_code(self, code) -> dict:
        sql = f'''
        SELECT *, p.id as promo_id FROM {self.table_name} p
        LEFT JOIN {self.promo_code_subscribes_prices_table_name} pcspi on p.id = pcspi.promocode_id
        LEFT JOIN {self.promo_code_users} pcu on p.id = pcu.promo_code_id
        WHERE p.promo_code='{code}';
        '''

        records = await self.fetch(sql)
        if not records:
            return {}

        promo_code = {
            'id': records[0]['promo_id'],
            'is_reusable': True if records[0]['time_mode'] == 'M' else False,
            'is_multi_user': True if records[0]['user_mode'] == 'M' else False,
            'promo_code': code,
            'discount': records[0]['discount'],
            'subscribes_ids': {record['subprice_id'] for record in records},
            'users': {record['user_id']: True if record['active'] == '1' else False for record in records if record['user_id']}
        }

        return promo_code

    async def cancel_promo(self, promo_code_id, telegram_id) -> None:
        sql = f'''
        DELETE FROM {self.promo_code_users}
        WHERE user_id=(SELECT id FROM {workers.UsersWorker.table_name} WHERE telegram_id={telegram_id}) AND promo_code_id={promo_code_id}
        '''

        await self.execute(sql)

    async def deactivate_user_promo_code(self, promo_code_id, user_id) -> None:
        sql = f'''
        UPDATE {self.promo_code_users}
        SET active='0'
        WHERE user_id={user_id} AND promo_code_id={promo_code_id}
        '''

        await self.execute(sql)

    async def add_user_to_promo_code(self, promo_code_id, telegram_id) -> None:
        sql = f'''
        INSERT INTO {self.promo_code_users} (active, promo_code_id, user_id)
        VALUES ('1', {promo_code_id}, (SELECT id FROM {workers.UsersWorker.table_name} WHERE telegram_id={telegram_id}))
        '''

        await self.execute(sql)
