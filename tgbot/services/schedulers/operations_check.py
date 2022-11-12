from aiogram import Bot

from tgbot.config import Config
from tgbot.services.db.database import Database
from tgbot.services.yoomoney import YooMoney
from tgbot.services.custom_broadcasters import MultilingualTextBroadcaster
import tgbot.keyboards.inline as inline_keyboards


async def check_operations(bot: Bot, db: Database, config: Config, yoomoney: YooMoney):
    await balance_accrual(bot, db, config, yoomoney)
    await subscribes_activation(bot, db, config, yoomoney)


async def balance_accrual(bot: Bot, db: Database, config: Config, yoomoney: YooMoney):
    operations = await db.operations_worker.get_operations_with_telegram_ids('top_up')

    telegram_ids_to_notify = set()
    for operation in operations:
        payment_status = yoomoney.check_payment(operation['payment_id'])

        if payment_status == 'succeeded':
            await db.users_worker.update_not_end_payment(operation['telegram_id'], False)
            await db.users_worker.update_balance(operation['telegram_id'], f'+{operation["top_up"]}')
            await db.users_worker.increase_deposit(operation['telegram_id'], operation['top_up'])
            await db.operations_worker.delete_operation(operation['id'])
            telegram_ids_to_notify.add(operation['telegram_id'])

        elif payment_status == 'canceled':
            await db.operations_worker.delete_operation(operation['id'])

    await MultilingualTextBroadcaster(
        chats=list(telegram_ids_to_notify),
        text='Уведомление об зачислении на баланс',
        reply_markup_callback=inline_keyboards.get_close_keyboard,
        bot=bot,
        database=db,
        config=config
    ).run()


async def subscribes_activation(bot: Bot, db: Database, config: Config, yoomoney: YooMoney):
    operations = await db.operations_worker.get_operations_with_telegram_ids('sub')

    telegram_ids_to_notify = set()
    for operation in operations:
        payment_status = yoomoney.check_payment(operation['payment_id'])

        if payment_status == 'succeeded':
            subscribes_price_id = operation['payload']
            subscribe = await db.subscribes_worker.get_subscribe_price(subscribes_price_id)
            await db.users_worker.increase_subscribe_time(operation['telegram_id'], subscribe['duration'])

            user_subscribe = await db.subscribes_worker.get_user_subscribe(operation['telegram_id'])
            if user_subscribe:
                await db.subscribes_worker.update_user_subscribe(operation['user_id'], subscribe['id'], subscribe['duration'])
            else:
                await db.subscribes_worker.add_user_subscribe(operation['user_id'], subscribe['id'], subscribe['duration'])

            promo_code = await db.promo_codes_worker.get_user_promo_code(user_id=operation['user_id'])
            if promo_code and promo_code['time_mode'] == 'O':
                await db.promo_codes_worker.deactivate_user_promo_code(promo_code['id'], operation['user_id'])

            await db.users_worker.update_subscribe_status(operation['telegram_id'], 3)
            await db.users_worker.update_not_end_payment(operation['telegram_id'], False)
            await db.users_worker.increase_deposit(operation['telegram_id'], operation['top_up'])
            await db.operations_worker.delete_operation(operation['id'])
            telegram_ids_to_notify.add(operation['telegram_id'])

        elif payment_status == 'canceled':
            await db.operations_worker.delete_operation(operation['id'])

    await MultilingualTextBroadcaster(
        chats=list(telegram_ids_to_notify),
        text='Уведомление о активации подписки',
        reply_markup_callback=inline_keyboards.get_close_keyboard,
        bot=bot,
        database=db,
        config=config
    ).run()
