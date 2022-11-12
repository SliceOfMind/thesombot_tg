from aiogram.utils.callback_data import CallbackData


languages = CallbackData('lang', 'code')
navigation = CallbackData('nav', 'to', 'payload')
fundraising_book = CallbackData('fund_book', 'book_id')
buy_fundraising_book = CallbackData('buy_fund_book', 'book_id', 'price')
change_show_progress = CallbackData('chg_show_progress', 'book_id')
vote_book = CallbackData('vote_book', 'action', 'book_id')
cancel = CallbackData('cancel', 'to')
payment_method_choose = CallbackData('pay_met_chs', 'method', 'action', 'amount', 'payload')
library = CallbackData('library', 'action', 'payload')
genre_choose = CallbackData('genre_choose', 'title', 'id')
search_book_choose = CallbackData('book_choose', 'book_id')
buy_archive_book = CallbackData('buy_archive_book', 'book_id', 'price')
close = CallbackData('close', 'is_final')
promo_code = CallbackData('promo_code', 'action')
