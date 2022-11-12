import asyncio

from aiogram import Bot

from tgbot.config import Config
from tgbot.services.db.database import Database
from tgbot.services.yoomoney import YooMoney
from tgbot.services.custom_broadcasters import MultilingualTextBroadcaster
import tgbot.keyboards.inline as inline_keyboards


async def check_subscribes(bot: Bot, db: Database, config: Config, yoomoney: YooMoney):
    expired_subscribes = await db.subscribes_worker.get_active_expired_subscribes_with_users()

    telegram_ids_to_expired_notify = set()
    telegram_ids_to_reactivate_notify = set()
    for subscribe in expired_subscribes:
        if subscribe['is_auto_pay']:
            subscribe_price = await db.subscribes_worker.get_subscribe_price(subscribe['sub_price_id'])
            user_promo_code = await db.promo_codes_worker.get_user_promo_code(subscribe['user_id'])

            price = subscribe_price['value']
            if user_promo_code:
                promo_code = await db.promo_codes_worker.get_promo_code(user_promo_code['promo_code'])
                if subscribe_price['id'] in promo_code['subscribes_ids']:
                    if not promo_code['is_reusable']:
                        await db.promo_codes_worker.deactivate_user_promo_code(promo_code['id'], subscribe['user_id'])

                    price = round(price * ((100 - promo_code['discount']) / 100))
                    if price == 0: price += 1

            payment_id = yoomoney.make_auto_payment(price, subscribe['payment_id'])
            await asyncio.sleep(5)
            payment_status = yoomoney.check_payment(payment_id)

            if payment_status == 'succeeded':
                await db.subscribes_worker.update_user_subscribe(subscribe['user_id'], subscribe_price['id'], subscribe_price['duration'])
                await db.users_worker.increase_subscribe_time(subscribe['telegram_id'], subscribe_price['duration'])
                await db.users_worker.increase_deposit(subscribe['telegram_id'], price)
                await db.users_worker.update_subscribe_status(subscribe['telegram_id'], 3)
                telegram_ids_to_reactivate_notify.add(subscribe['telegram_id'])
                continue

        await db.subscribes_worker.deactivate_user_subscribe(subscribe['user_id'])
        await db.users_worker.update_subscribe_status(subscribe['telegram_id'], 2)
        telegram_ids_to_expired_notify.add(subscribe['telegram_id'])

    await MultilingualTextBroadcaster(
        chats=list(telegram_ids_to_expired_notify),
        text='Уведомление об окончании подписки',
        reply_markup_callback=inline_keyboards.get_close_keyboard,
        bot=bot,
        database=db,
        config=config
    ).run()

    await MultilingualTextBroadcaster(
        chats=list(telegram_ids_to_reactivate_notify),
        text='Уведомление о продлении подписки',
        reply_markup_callback=inline_keyboards.get_close_keyboard,
        bot=bot,
        database=db,
        config=config
    ).run()
