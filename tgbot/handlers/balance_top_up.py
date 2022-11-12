from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message

import tgbot.keyboards.inline as inline_keyboards
import tgbot.misc.callbacks as callbacks
import tgbot.misc.states as states
from tgbot.services.db.database import Database
from tgbot.services.yoomoney import YooMoney


async def start_top_up_amount_input(call: CallbackQuery, state: FSMContext):
    _ = call.bot.get('_')
    db = call.bot.get('database')

    settings = (await db.settings_worker.select())[0]

    await call.message.edit_text(_('Приглашение ко вводу суммы пополнения').format(limit=settings['top_up_limit']),
                                 reply_markup=inline_keyboards.get_cancel_keyboard(_, to='balance'))
    await state.update_data(limit=settings['top_up_limit'], format_error=False, limit_error=False)
    await states.TopUpState.waiting_for_input.set()
    await call.answer()


async def get_top_up_amount(message: Message, state: FSMContext):
    _ = message.bot.get('_')
    redis = message.bot.get('redis')

    main_menu_id = int(await redis.get(name=str(message.from_id)))

    await message.delete()

    async with state.proxy() as data:
        format_error = data['format_error']
        limit_error = data['limit_error']
        limit = data['limit']

    if not message.text.isdigit():
        if not format_error:
            error_text = _('Ошибка неверный формат ввода') + '\n\n'
            await message.bot.edit_message_text(
                chat_id=message.from_id,
                message_id=main_menu_id,
                text=error_text + _('Приглашение ко вводу суммы пополнения').format(limit=limit),
                reply_markup=inline_keyboards.get_cancel_keyboard(_, to='balance')
            )
            await state.update_data(format_error=True)
        return

    if format_error:
        await state.update_data(format_error=False)

    top_up_amount = int(message.text)
    if top_up_amount > int(limit):
        if not limit_error:
            error_text = _('Ошибка слишком большая сумма') + '\n\n'
            await message.bot.edit_message_text(
                chat_id=message.from_id,
                message_id=main_menu_id,
                text=error_text + _('Приглашение ко вводу суммы пополнения').format(limit=limit),
                reply_markup=inline_keyboards.get_cancel_keyboard(_, to='balance')
            )
            await state.update_data(limit_error=True)
        return

    await message.bot.edit_message_text(
        chat_id=message.from_id,
        message_id=main_menu_id,
        text=_('Меню выбора способа оплаты'),
        reply_markup=inline_keyboards.get_choose_payment_method_keyboard(_, 'top_up', top_up_amount)
    )
    await state.finish()


async def show_top_up_pay_menu(call: CallbackQuery, callback_data: dict):
    _ = call.bot.get('_')
    db: Database = call.bot.get('database')
    yoomoney: YooMoney = call.bot.get('yoomoney')

    payment_id, payment_url = yoomoney.make_onetime_payment(amount=callback_data['amount'],
                                                            description=_('Описание платежа пополнения'))

    _('Уведомление об зачислении на баланс')  # So that pybabel can find string
    await db.users_worker.update_not_end_payment(call.from_user.id, True)
    await db.operations_worker.add_operation(call.from_user.id, payment_id, callback_data['amount'], 'top_up')

    await call.message.edit_text(_('Меню оплаты'), reply_markup=inline_keyboards.get_pay_keyboard(_, payment_url, 'balance'))
    await call.answer()


def register_balance_top_up(dp: Dispatcher):
    dp.register_callback_query_handler(start_top_up_amount_input, text='top_up')
    dp.register_message_handler(get_top_up_amount, state=states.TopUpState.waiting_for_input)
    dp.register_callback_query_handler(show_top_up_pay_menu, callbacks.payment_method_choose.filter(action='top_up', method='yookassa'))
