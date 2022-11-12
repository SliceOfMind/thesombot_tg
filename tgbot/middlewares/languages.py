from typing import Tuple, Any, Optional

from aiogram.contrib.middlewares.i18n import I18nMiddleware
from aiogram import types

from tgbot.services.db.database import Database


class ACLMiddleware(I18nMiddleware):
    async def get_user_locale(self, action: str, args: Tuple[Any]) -> Optional[str]:
        telegram_user = types.User.get_current()

        db: Database = telegram_user.bot.get('database')
        database_user = await db.users_worker.get_user_by_telegram_id(telegram_user.id)
        if database_user:
            lang = await db.users_worker.get_user_language_code(telegram_user.id)
        else:
            lang = 'en'

        return lang
