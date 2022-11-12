from aiogram.dispatcher.filters.state import State, StatesGroup


class PromoCodeState(StatesGroup):
    waiting_for_input = State()


class QuestionState(StatesGroup):
    waiting_for_input = State()


class VoteState(StatesGroup):
    waiting_for_input = State()


class TopUpState(StatesGroup):
    waiting_for_input = State()


class LibraryState(StatesGroup):
    in_menu = State()
    waiting_for_year_input = State()
    waiting_for_title_input = State()
    waiting_for_author_input = State()
    waiting_for_genre_choice = State()
