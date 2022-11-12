from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message

from tgbot.handlers.main_menu import show_subscribes_menu
from tgbot.services.db.database import Database
import tgbot.misc.callbacks as callbacks
import tgbot.keyboards.inline as inline_keyboards
import tgbot.misc.states as states
from tgbot.services.yoomoney import YooMoney


async def change_auto_pay(call: CallbackQuery):
    _ = call.bot.get('_')
    db: Database = call.bot.get('database')

    auto_pay = await db.users_worker.change_auto_pay(call.from_user.id)
    if auto_pay:
        await call.answer(_('Автоплатёж включён'), show_alert=True)
    else:
        await call.answer(_('Автоплатёж выключен'), show_alert=True)

    await show_subscribes_menu(call)


async def cancel_promo_code(call: CallbackQuery):
    _ = call.bot.get('_')
    db: Database = call.bot.get('database')

    promo_code = await db.promo_codes_worker.get_user_promo_code(telegram_id=call.from_user.id)
    await db.promo_codes_worker.cancel_promo(promo_code['id'], call.from_user.id)
    await call.answer(_('Промокод отменён'), show_alert=True)
    await show_subscribes_menu(call)


async def start_promo_code_input(call: CallbackQuery, state: FSMContext):
    _ = call.bot.get('_')
    db: Database = call.bot.get('database')

    settings = (await db.settings_worker.select())[0]
    await state.update_data(limit_error=False, not_exist_error=False, already_used_error=False, limit=settings['promo_code_limit'])
    await states.PromoCodeState.waiting_for_input.set()
    await call.message.edit_text(_('Приглашение ко вводу промокода').format(limit=settings['promo_code_limit']),
                                 reply_markup=inline_keyboards.get_cancel_keyboard(_, to='subscribes'))
    await call.answer()


async def get_promo_code(message: Message, state: FSMContext):
    _ = message.bot.get('_')
    db: Database = message.bot.get('database')
    redis = message.bot.get('redis')

    main_menu_id = int(await redis.get(name=str(message.from_id)))
    user = await db.users_worker.get_user_by_telegram_id(message.from_id)

    await message.delete()

    async with state.proxy() as data:
        limit = data['limit']
        limit_error = data['limit_error']
        already_used_error = data['already_used_error']
        not_exist_error = data['not_exist_error']

    if len(message.text) > limit:
        if not limit_error:
            error_text = _('Ошибка слишком много символов в тексте') + '\n\n'
            await message.bot.edit_message_text(
                chat_id=message.from_id,
                message_id=main_menu_id,
                text=error_text + _('Приглашение ко вводу промокода').format(limit=limit),
                reply_markup=inline_keyboards.get_cancel_keyboard(_, to='subscribes')
            )
            await state.update_data(limit_error=True, not_exist_error=False, already_used_error=False)
        return

    if limit_error:
        await state.update_data(limit_error=False)

    promo_code = await db.promo_codes_worker.get_promo_code(message.text)
    if not promo_code:
        if not not_exist_error:
            error_text = _('Ошибка промокод не существует') + '\n\n'
            await message.bot.edit_message_text(
                chat_id=message.from_id,
                message_id=main_menu_id,
                text=error_text + _('Приглашение ко вводу промокода').format(limit=limit),
                reply_markup=inline_keyboards.get_cancel_keyboard(_, to='subscribes')
            )
            await state.update_data(not_exist_error=True, limit_error=False, already_used_error=False)
        return

    if not_exist_error:
        await state.update_data(not_exist_error=False)

    if (not promo_code['is_multi_user'] and len(promo_code['users']) != 0) or user['id'] in promo_code['users']:
        if not already_used_error:
            error_text = _('Ошибка промокод уже использован') + '\n\n'
            await message.bot.edit_message_text(
                chat_id=message.from_id,
                message_id=main_menu_id,
                text=error_text + _('Приглашение ко вводу промокода').format(limit=limit),
                reply_markup=inline_keyboards.get_cancel_keyboard(_, to='subscribes')
            )
            await state.update_data(not_exist_error=False, limit_error=False, already_used_error=True)
        return

    await db.promo_codes_worker.add_user_to_promo_code(promo_code['id'], message.from_id)
    await state.finish()

    await message.bot.edit_message_text(
        chat_id=message.from_id,
        message_id=main_menu_id,
        text=_('Уведомление об успешном применении промокода'),
        reply_markup=inline_keyboards.get_back_keyboard(_, to='subscribes')
    )


async def buy_subscribe(call: CallbackQuery, callback_data: dict):
    _ = call.bot.get('_')
    db: Database = call.bot.get('database')
    yoomoney: YooMoney = call.bot.get('yoomoney')

    payment_method_id, payment_id, payment_link = yoomoney.make_auto_payment_init(callback_data['amount'], 'bank_card', _('Описание платежа с подпиской'))
    await db.operations_worker.add_operation(call.from_user.id, payment_id, callback_data['amount'], 'sub', callback_data['payload'])
    await db.users_worker.update_not_end_payment(call.from_user.id, True)
    await db.users_worker.update_payment_method(call.from_user.id, payment_method_id)

    _('Уведомление о активации подписки')  # So that pybabel can find string
    _('Уведомление о продлении подписки')  # So that pybabel can find string
    _('Уведомление об окончании подписки')  # So that pybabel can find string

    await call.message.edit_text(_('Меню оплаты'), reply_markup=inline_keyboards.get_pay_keyboard(_, payment_link, 'subscribes'))
    await call.answer()


def register_subscribes(dp: Dispatcher):
    dp.register_callback_query_handler(change_auto_pay, text='change_auto_pay')
    dp.register_callback_query_handler(cancel_promo_code, callbacks.promo_code.filter(action='cancel'))
    dp.register_callback_query_handler(start_promo_code_input, callbacks.promo_code.filter(action='use'))
    dp.register_message_handler(get_promo_code, state=states.PromoCodeState.waiting_for_input)
    dp.register_callback_query_handler(buy_subscribe, callbacks.payment_method_choose.filter(action='sub', method='bank_card'))
