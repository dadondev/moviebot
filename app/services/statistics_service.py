"""Statistics service."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories import (
    FavoriteRepository,
    MovieRepository,
    MovieRequestRepository,
    RatingRepository,
    UserRepository,
)


class StatisticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.movie_repo = MovieRepository(session)
        self.request_repo = MovieRequestRepository(session)
        self.rating_repo = RatingRepository(session)
        self.favorite_repo = FavoriteRepository(session)

    async def get_summary(self) -> dict:
        now = datetime.now(UTC)
        today = now - timedelta(days=1)
        active_since = now - timedelta(days=7)

        total_users = await self.user_repo.count_all()
        active_users = await self.user_repo.count_active(active_since)
        total_movies = await self.movie_repo.count_all()
        total_views = await self.movie_repo.total_views()
        pending_requests = await self.request_repo.count_by_status("pending")
        new_users_today = await self.user_repo.count_created_since(today)
        new_movies_today = await self.movie_repo.count_created_since(today)

        most_viewed = await self.movie_repo.most_viewed()
        most_rated = await self.rating_repo.most_rated()
        most_favorited = await self.favorite_repo.most_favorited()

        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_movies": total_movies,
            "total_views": total_views,
            "pending_requests": pending_requests,
            "new_users_today": new_users_today,
            "new_movies_today": new_movies_today,
            "most_viewed": most_viewed,
            "most_rated": most_rated,
            "most_favorited": most_favorited,
        }
