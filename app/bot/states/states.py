"""FSM states for movie upload and admin flows."""

from aiogram.fsm.state import State, StatesGroup


class MovieUploadStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_original_title = State()
    waiting_for_code = State()
    waiting_for_description = State()
    waiting_for_year = State()
    waiting_for_genres = State()
    waiting_for_country = State()
    waiting_for_duration = State()
    waiting_for_imdb = State()
    waiting_for_age_rating = State()
    waiting_for_poster = State()
    waiting_for_trailer = State()
    waiting_for_series = State()
    confirmation = State()


class EpisodeAddStates(StatesGroup):
    waiting_for_file = State()
    waiting_for_episode_number = State()
    confirmation = State()


class MovieEditStates(StatesGroup):
    waiting_for_field = State()


class ChannelAddStates(StatesGroup):
    waiting_for_channel_id = State()
    waiting_for_title = State()
    waiting_for_invite_url = State()
    confirmation = State()


class GenreAddStates(StatesGroup):
    waiting_for_name = State()


class BroadcastStates(StatesGroup):
    waiting_for_message = State()


class SearchStates(StatesGroup):
    waiting_for_query = State()


class RequestStates(StatesGroup):
    waiting_for_title = State()
