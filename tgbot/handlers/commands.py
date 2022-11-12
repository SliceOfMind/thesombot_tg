from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from aiogram.utils.exceptions import MessageCantBeDeleted, MessageToDeleteNotFound
from aioredis import Redis

from tgbot.services.db.database import Database
import tgbot.keyboards.inline as inline_keyboards


async def start(message: Message, state: FSMContext):
    db: Database = message.bot.get('database')
    redis = message.bot.get('redis')
    _ = message.bot.get('_')

    is_user_exists = await db.users_worker.get_user_by_telegram_id(message.from_id)

    if is_user_exists:
        await send_main_menu(message, state)
        return

    referral_telegram_id = message.get_args()
    if referral_telegram_id and int(referral_telegram_id) == int(message.from_id):
        referral_telegram_id = None

    await db.users_worker.add_new_user(message.from_id, message.from_user.username, message.from_user.mention,
                                       referral_telegram_id)

    languages = await db.languages_worker.select()
    languages = [(lang['language_code'], lang['name']) for lang in languages]

    await message.delete()
    main_menu = await message.answer(_('Выбор языка'), reply_markup=inline_keyboards.get_choose_language_keyboard(languages))
    await redis.set(name=str(message.chat.id), value=main_menu.message_id)


async def send_main_menu(message: Message, state: FSMContext):
    _ = message.bot.get('_')
    redis: Redis = message.bot.get('redis')

    await state.finish()
    await message.delete()
    last_menu_id = await redis.get(name=str(message.chat.id))
    if last_menu_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=int(last_menu_id))
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass

    new_last_menu = await message.answer(_('Главное меню'), reply_markup=inline_keyboards.get_main_menu_keyboard(_))
    await redis.set(name=str(message.chat.id), value=new_last_menu.message_id)


def register_commands(dp: Dispatcher):
    dp.register_message_handler(start, commands=['start'], state='*')
    dp.register_message_handler(send_main_menu, commands=['menu'], state='*')
