import logging

import tgbot.services.db.workers as workers


class Database:
    """
    Interface for interacting with workers.
    Each worker has his own pool
    """

    def __init__(self, password: str, user: str, database: str, host: str = 'localhost', port: int = 5432):
        self.host = host
        self.password = password
        self.user = user
        self.database = database
        self.port = port

        self._connect_data = {
            'host': host,
            'password': password,
            'database': database,
            'user': user,
            'port': port
        }

        self.users_worker = workers.UsersWorker(**self._connect_data)
        self.languages_worker = workers.LanguagesWorker(**self._connect_data)
        self.subscribes_worker = workers.SubscribesWorker(**self._connect_data)
        self.books_worker = workers.BooksWorker(**self._connect_data)
        self.settings_worker = workers.SettingsWorker(**self._connect_data)
        self.questions_worker = workers.QuestionsWorker(**self._connect_data)
        self.votes_worker = workers.VotesWorker(**self._connect_data)
        self.archive_worker = workers.ArchiveWorker(**self._connect_data)
        self.statistic_worker = workers.StatisticWorker(**self._connect_data)
        self.operations_worker = workers.OperationsWorker(**self._connect_data)
        self.posts_worker = workers.PostsWorker(**self._connect_data)
        self.promo_codes_worker = workers.PromoCodesWorker(**self._connect_data)

        self.workers = [
            self.users_worker,
            self.languages_worker,
            self.subscribes_worker,
            self.books_worker,
            self.settings_worker,
            self.questions_worker,
            self.votes_worker,
            self.archive_worker,
            self.statistic_worker,
            self.operations_worker,
            self.posts_worker,
            self.promo_codes_worker
        ]

        self.logger = logging.getLogger(__name__)

    async def create_all(self):
        [await worker.create() for worker in self.workers]

        self.logger.debug('All tables created')

    async def drop_all(self):
        [await worker.drop() for worker in self.workers]

        self.logger.debug('All tables dropped')

    async def truncate_all(self):
        [await worker.truncate() for worker in self.workers]

        self.logger.debug('All tables truncated')

    async def close_pools(self):
        [await worker.pool.close() for worker in self.workers if worker.pool]

        self.logger.debug('All pools closed')
