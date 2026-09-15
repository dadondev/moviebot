"""Repositories package."""

from app.database.repositories.favorite_repository import FavoriteRepository
from app.database.repositories.genre_repository import GenreRepository
from app.database.repositories.movie_file_repository import MovieFileRepository
from app.database.repositories.movie_repository import MovieRepository
from app.database.repositories.movie_request_repository import MovieRequestRepository
from app.database.repositories.rating_repository import RatingRepository
from app.database.repositories.required_channel_repository import (
    RequiredChannelRepository,
)
from app.database.repositories.settings_repository import SettingsRepository
from app.database.repositories.user_repository import UserRepository

__all__ = [
    "UserRepository",
    "MovieRepository",
    "GenreRepository",
    "MovieFileRepository",
    "FavoriteRepository",
    "RatingRepository",
    "MovieRequestRepository",
    "RequiredChannelRepository",
    "SettingsRepository",
]
