from dataclasses import dataclass
from pathlib import Path

from environs import Env


@dataclass
class DatabaseConfig:
    host: str
    port: int
    password: str
    user: str
    database: str


@dataclass
class TelegramBot:
    token: str
    use_redis: bool
    extended_logs: bool


@dataclass
class Miscellaneous:
    i18n_domain: str
    base_dir: Path
    locales_dir: Path
    web_base_dir: str

    genres_rows_per_page: int
    genres_in_row: int
    search_books_per_page: int


@dataclass
class YooMoney:
    account_id: str
    secret_key: str
    return_url: str


@dataclass
class Schedulers:
    updates_from_server_interval: int
    operations_check_interval: int
    subscribes_check_interval: int
    other_interval: int


@dataclass
class Config:
    telegram_bot: TelegramBot
    database: DatabaseConfig
    misc: Miscellaneous
    yoomoney: YooMoney
    schedulers: Schedulers


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        telegram_bot=TelegramBot(
            token=env.str('BOT_TOKEN'),
            use_redis=env.bool('USE_REDIS'),
            extended_logs=env.bool('EXTENDED_LOGS')
        ),
        database=DatabaseConfig(
            host=env.str('DB_HOST'),
            port=env.int('DB_PORT'),
            password=env.str('DB_PASS'),
            user=env.str('DB_USER'),
            database=env.str('DB_NAME')
        ),
        misc=Miscellaneous(
            i18n_domain=env.str('I18N_DOMAIN'),
            base_dir=Path(__file__).parent,
            locales_dir=Path(__file__).parent / 'locales',

            genres_in_row=env.int('GENRES_IN_ROW'),
            genres_rows_per_page=env.int('GENRES_ROWS_PER_PAGE'),
            search_books_per_page=env.int('SEARCH_BOOKS_PER_PAGE'),
            web_base_dir=env.str('WEB_BASE_DIR')
        ),
        yoomoney=YooMoney(
            account_id=env.str('ACCOUNT_ID'),
            secret_key=env.str('SECRET_KEY'),
            return_url=env.str('RETURN_URL')
        ),
        schedulers=Schedulers(
            updates_from_server_interval=env.int('UPDATES_FROM_SERVER_INTERVAL'),
            operations_check_interval=env.int('OPERATIONS_CHECK_INTERVAL'),
            subscribes_check_interval=env.int('SUBSCRIBES_CHECK_INTERVAL'),
            other_interval=env.int('OTHER_INTERVAL')
        )
    )
