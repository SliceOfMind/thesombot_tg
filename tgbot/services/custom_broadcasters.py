import asyncio
import gettext
from io import BytesIO

import aiofiles as aiofiles
from aiogram import Bot
from aiogram.types import InputFile
from aiogram_broadcaster.base import BaseBroadcaster
from aiogram_broadcaster.types import ChatIdType, ChatsType, MarkupType
from aiogram.utils import exceptions

from tgbot.config import Config
from tgbot.services.db.database import Database


class LanguageContext:
    def __init__(self, user_telegram_id, database: Database, config: Config):
        self.telegram_id = user_telegram_id
        self.db = database
        self.config = config

    async def __aenter__(self):
        lang_code = await self.db.users_worker.get_user_language_code(self.telegram_id)
        lang_translations = gettext.translation(
            self.config.misc.i18n_domain,
            localedir=self.config.misc.locales_dir,
            languages=[lang_code]
        )
        lang_translations.install()

        return lang_translations.gettext

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            raise


class MultilingualTextBroadcaster(BaseBroadcaster):
    def __init__(
            self,
            chats: ChatsType,
            text: str,
            kwargs: dict = None,
            text_kwargs: dict = None,
            reply_kwargs: dict = None,
            parse_mode: str = None,
            disable_web_page_preview: bool = None,
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            allow_sending_without_reply: bool = None,
            reply_markup: MarkupType = None,
            reply_markup_callback=None,
            bot: Bot = None,
            database: Database = None,
            config: Config = None,
            bot_token: str = None,
            timeout: float = 0.02,
            logger=__name__
    ):
        super().__init__(
            chats=chats,
            kwargs=kwargs,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
            bot=bot,
            bot_token=bot_token,
            timeout=timeout,
            logger=logger
        )

        if reply_kwargs is None:
            reply_kwargs = dict()
        if text_kwargs is None:
            text_kwargs = dict()

        self.reply_markup_callback = reply_markup_callback
        self.text_kwargs = text_kwargs
        self.reply_kwargs = reply_kwargs
        self.db = database
        self.config = config
        self.text = text
        self.parse_mode = parse_mode
        self.disable_web_page_preview = disable_web_page_preview

    async def send(self, chat_id: ChatIdType, chat_args: dict) -> bool:
        try:
            async with LanguageContext(chat_id, self.db, self.config) as _:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=_(self.text).format(**self.text_kwargs),
                    parse_mode=self.parse_mode,
                    disable_web_page_preview=self.disable_web_page_preview,
                    disable_notification=self.disable_notification,
                    reply_to_message_id=self.reply_to_message_id,
                    allow_sending_without_reply=self.allow_sending_without_reply,
                    reply_markup=self.reply_markup_callback(_, **self.reply_kwargs)
                )
        except exceptions.RetryAfter as e:
            self.logger.debug(
                f'Target [ID:{chat_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.'
            )
            await asyncio.sleep(e.timeout)
            return await self.send(chat_id, chat_args)  # Recursive call
        except (
                exceptions.ChatNotFound,
                exceptions.UserDeactivated,
                exceptions.ChatNotFound
        ) as e:
            self.logger.debug(f'Target [ID:{chat_id}]: {e.match}')
        except exceptions.BotBlocked:
            await self.db.users_worker.update_is_block(chat_id, True)
            self.logger.debug(f'Target [ID:{chat_id}]: bot blocked')
        except exceptions.TelegramAPIError:
            self.logger.exception(f'Target [ID:{chat_id}]: failed')
        else:
            self.logger.debug(f'Target [ID:{chat_id}]: success')
            return True
        return False


class PollBroadcaster(BaseBroadcaster):
    def __init__(
            self,
            chats: ChatsType,
            question: str,
            options: list[str],
            is_anonymous: bool = None,
            is_closed: bool = None,
            type: str = None,
            allows_multiple_answers: bool = None,
            correct_option_id: int = None,
            open_period: int = None,
            kwargs: dict = None,
            text_kwargs: dict = None,
            reply_kwargs: dict = None,
            parse_mode: str = None,
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            allow_sending_without_reply: bool = None,
            reply_markup: MarkupType = None,
            reply_markup_callback=None,
            bot: Bot = None,
            database: Database = None,
            config: Config = None,
            bot_token: str = None,
            timeout: float = 0.02,
            logger=__name__
    ):
        super().__init__(
            chats=chats,
            kwargs=kwargs,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
            bot=bot,
            bot_token=bot_token,
            timeout=timeout,
            logger=logger
        )

        if reply_kwargs is None:
            reply_kwargs = dict()
        if text_kwargs is None:
            text_kwargs = dict()

        self.reply_markup_callback = reply_markup_callback
        self.text_kwargs = text_kwargs
        self.reply_kwargs = reply_kwargs
        self.db = database
        self.config = config
        self.question = question
        self.options = options
        self.parse_mode = parse_mode
        self.is_anonymous = is_anonymous
        self.type = type
        self.allows_multiple_answers = allows_multiple_answers
        self.correct_option_id = correct_option_id
        self.is_closed = is_closed
        self.open_period = open_period
        self.poll_ids = dict()

    async def send(self, chat_id: ChatIdType, chat_args: dict) -> bool:
        try:
            async with LanguageContext(chat_id, self.db, self.config) as _:
                msg = await self.bot.send_poll(
                    chat_id=chat_id,
                    question=self.question.format(**self.text_kwargs),
                    options=self.options,
                    is_anonymous=self.is_anonymous,
                    type=self.type,
                    is_closed=self.is_closed,
                    open_period=self.open_period,
                    allows_multiple_answers=self.allows_multiple_answers,
                    correct_option_id=self.correct_option_id,
                    disable_notification=self.disable_notification,
                    reply_to_message_id=self.reply_to_message_id,
                    allow_sending_without_reply=self.allow_sending_without_reply,
                    reply_markup=self.reply_markup_callback(_, **self.reply_kwargs)
                )
                self.poll_ids[chat_id] = msg.poll.id

        except exceptions.RetryAfter as e:
            self.logger.debug(
                f'Target [ID:{chat_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.'
            )
            await asyncio.sleep(e.timeout)
            return await self.send(chat_id, chat_args)  # Recursive call
        except (
                exceptions.ChatNotFound,
                exceptions.UserDeactivated,
                exceptions.ChatNotFound
        ) as e:
            self.logger.debug(f'Target [ID:{chat_id}]: {e.match}')
        except exceptions.BotBlocked:
            await self.db.users_worker.update_is_block(chat_id, True)
            self.logger.debug(f'Target [ID:{chat_id}]: bot blocked')
        except exceptions.TelegramAPIError:
            self.logger.exception(f'Target [ID:{chat_id}]: failed')
        else:
            self.logger.debug(f'Target [ID:{chat_id}]: success')
            return True
        return False


class FileBroadcaster(BaseBroadcaster):
    document_files = ('doc', 'docx', 'pdf', 'xlsx', 'xls')
    image_files = ('png', 'jpg', 'jpeg', 'gif')

    def __init__(
            self,
            chats: ChatsType,
            caption: str,
            file_path: str,
            kwargs: dict = None,
            text_kwargs: dict = None,
            reply_kwargs: dict = None,
            parse_mode: str = None,
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            allow_sending_without_reply: bool = None,
            reply_markup: MarkupType = None,
            reply_markup_callback=None,
            bot: Bot = None,
            database: Database = None,
            config: Config = None,
            bot_token: str = None,
            timeout: float = 0.02,
            logger=__name__
    ):
        super().__init__(
            chats=chats,
            kwargs=kwargs,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
            bot=bot,
            bot_token=bot_token,
            timeout=timeout,
            logger=logger
        )

        if reply_kwargs is None:
            reply_kwargs = dict()
        if text_kwargs is None:
            text_kwargs = dict()

        self.reply_markup_callback = reply_markup_callback
        self.text_kwargs = text_kwargs
        self.reply_kwargs = reply_kwargs
        self.db = database
        self.config = config
        self.caption = caption
        self.file_path = file_path
        self.file_id = None
        self.parse_mode = parse_mode

    async def send(self, chat_id: ChatIdType, chat_args: dict) -> bool:
        try:
            async with LanguageContext(chat_id, self.db, self.config) as _:
                if not self.file_id:
                    async with aiofiles.open(self.file_path, 'rb') as file:
                        file = InputFile(BytesIO(await file.read()), filename=self.file_path.split('\\')[-1])
                else:
                    file = self.file_id
                if self.file_path.split('.')[-1] in self.document_files:
                    msg = await self.bot.send_document(
                        chat_id=chat_id,
                        caption=self.caption.format(**self.text_kwargs),
                        document=file,
                        parse_mode=self.parse_mode,
                        disable_notification=self.disable_notification,
                        allow_sending_without_reply=self.allow_sending_without_reply,
                        reply_to_message_id=self.reply_to_message_id,
                        reply_markup=self.reply_markup_callback(_, **self.reply_kwargs)
                    )
                    if not self.file_id:
                        self.file_id = msg.document.file_id
                elif self.file_path.split('.')[-1] in self.image_files:
                    msg = await self.bot.send_photo(
                        chat_id=chat_id,
                        caption=self.caption.format(**self.text_kwargs),
                        photo=file,
                        parse_mode=self.parse_mode,
                        disable_notification=self.disable_notification,
                        allow_sending_without_reply=self.allow_sending_without_reply,
                        reply_to_message_id=self.reply_to_message_id,
                        reply_markup=self.reply_markup_callback(_, **self.reply_kwargs)
                    )
                    if not self.file_id:
                        self.file_id = msg.photo[-1].file_id

        except exceptions.RetryAfter as e:
            self.logger.debug(
                f'Target [ID:{chat_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.'
            )
            await asyncio.sleep(e.timeout)
            return await self.send(chat_id, chat_args)  # Recursive call
        except (
                exceptions.ChatNotFound,
                exceptions.UserDeactivated,
                exceptions.ChatNotFound
        ) as e:
            self.logger.debug(f'Target [ID:{chat_id}]: {e.match}')
        except exceptions.BotBlocked:
            await self.db.users_worker.update_is_block(chat_id, True)
            self.logger.debug(f'Target [ID:{chat_id}]: bot blocked')
        except exceptions.TelegramAPIError:
            self.logger.exception(f'Target [ID:{chat_id}]: failed')
        else:
            self.logger.debug(f'Target [ID:{chat_id}]: success')
            return True
        return False
