"""ORM models package. Importing this registers all models on Base.metadata."""

from app.database.models.favorite import Favorite, Rating
from app.database.models.movie import Genre, Movie, MovieFile, movie_genres
from app.database.models.request_channel import (
    MovieRequest,
    RequiredChannel,
    Setting,
)
from app.database.models.user import User

__all__ = [
    "User",
    "Movie",
    "Genre",
    "MovieFile",
    "movie_genres",
    "Favorite",
    "Rating",
    "MovieRequest",
    "RequiredChannel",
    "Setting",
]
