import uuid
import logging

from yookassa import Configuration, Payment

from tgbot.config import Config


class YooMoney:
    def __init__(self, config: Config):
        self.config = config

        Configuration.account_id = config.yoomoney.account_id
        Configuration.secret_key = config.yoomoney.secret_key

        self.logger = logging.getLogger(__name__)

    def check_payment(self, payment_id: str) -> str:
        """
        Возвращает статус платежа

        :param payment_id: Идентификатор платежа
        :return: Статус платежа. Возможные значения: pending, waiting_for_capture, succeeded и canceled.
        """
        self.logger.debug(f'check_payment | {payment_id}')
        try:
            payment = Payment.find_one(payment_id)
            self.logger.debug(f'check_payment | {payment_id} | {payment.status}')
            return payment.status
        except Exception as e:
            self.logger.error(f'Can\'t find payment with id - {payment_id} with error - {e}')

    def make_onetime_payment(self, amount: int, description: str = 'Пополнение баланса') -> (str, str):
        """
        Создает платеж в YooMoney

        :param amount: Сумма платежа
        :param description: Описание платежа для пользователя
        :return: Возвращает идентификатор для отслеживания статуса платежа, ссылку для оплаты
        """
        self.logger.debug(f'make_onetime_payment | {amount}')
        try:
            payment = Payment.create({
                'amount': {
                    'value': float(amount),
                    'currency': 'RUB'
                },
                'confirmation': {
                    'type': 'redirect',
                    'return_url': self.config.yoomoney.return_url
                },
                'capture': True,
                'description': description
            }, uuid.uuid4())
            self.logger.debug(f'make_onetime_payment | {payment.id} | {payment.confirmation.confirmation_url}')
            return payment.id, payment.confirmation.confirmation_url
        except Exception as e:
            self.logger.error(f'make_onetime_payment | {amount} | error - {e}')

    def make_auto_payment_init(self, amount: int, pay_type: str, description: str = 'Подписка'):
        """
        Создает платеж с сохранением способа оплаты для автоплатежа в YooMoney

        :param amount: Сумма платежа
        :param pay_type: Один из типов: bank_card, apple_pay, google_pay, yoo_money
        :param description: Описание платежа для пользователя
        :return: Возвращает идентификатора сохраненного способа оплаты, ссылку для оплаты
        """
        self.logger.debug(f'make_auto_payment_init | {amount} | {pay_type}')
        try:
            payment = Payment.create({
                'amount': {
                    'value': float(amount),
                    'currency': 'RUB'
                },
                'payment_method_data': {
                    'type': pay_type
                },
                'confirmation': {
                    'type': 'redirect',
                    'return_url': self.config.yoomoney.return_url
                },
                'capture': True,
                'description': description,
                'save_payment_method': True
            })
            self.logger.debug(f'make_auto_payment_init {payment.id} | {payment.confirmation.confirmation_url}')
            return payment.payment_method.id, payment.id, payment.confirmation.confirmation_url
        except Exception as e:
            self.logger.error(f'make_auto_payment_init | {amount} | {pay_type} | error - {e}')
            
    def make_auto_payment(self, amount: int, payment_method_id: str, description: str = 'Подписка') -> str:
        """
        Создает повторный автоплатеж в YooMoney

        :param amount: Сумма платежа
        :param payment_method_id: Идентификатор сохраненного метода оплаты
        :param description: Описание платежа для пользователя
        :return: Возвращает идентификатор для отслеживания статуса платежа
        """
        self.logger.debug(f'make_auto_payment | {amount} | {payment_method_id}')
        try:
            payment = Payment.create({
                'amount': {
                    'value': float(amount),
                    'currency': 'RUB'
                },
                'capture': True,
                'payment_method_id': payment_method_id,
                'description': description
            })
            self.logger.debug(f'make_auto_payment | {payment.id}')
            return payment.id  # не принимает карты с 3d secure
        except Exception as e:
            self.logger.error(f'make_auto_payment | {amount} | {payment_method_id} | error - {e}')
