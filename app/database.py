import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy import select, update
from app.models.database import (
    Base,
    GuildSettings,
    GuildSettingsSchema,
    GuildSettingUpdate,
    ThreadSettings,
)
from app.models.links import LinkEntry
from app.models.slaps import SlapEntry
from sqlalchemy import func

from app.utils.logger import get_logger

logger = get_logger(__name__)


class Database:
    def __init__(self, db_url: str | None = None):
        if db_url is None:
            base_dir = Path(__file__).resolve().parent
            db_url = f"sqlite+aiosqlite:///{base_dir / 'guild_settings.db'}"
        self.db_url = db_url
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None

    def backup_and_reset_database(self) -> None:
        """Backup existing database and prepare for fresh creation."""
        if not self.db_url.startswith("sqlite"):
            logger.warning("⚠️ Database backup only supported for SQLite databases")
            return

        db_path = self.db_url.replace("sqlite+aiosqlite:///", "")
        db_file = Path(db_path)

        if db_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = (
                db_file.parent / f"{db_file.stem}_backup_{timestamp}{db_file.suffix}"
            )

            try:
                shutil.copy2(db_file, backup_path)
                logger.info(f"📦 Database backed up to: {backup_path}")

                db_file.unlink()
                logger.info(f"🗑️ Original database removed: {db_file}")

            except Exception as e:
                logger.error(f"❌ Failed to backup database: {e}")
                raise
        else:
            logger.info("ℹ️ No existing database found to backup")

    async def connect(self, reset_database: bool = False) -> None:
        """Initialize database connection and create tables if they don't exist."""
        try:
            if reset_database:
                logger.info("🔄 Database reset requested")
                self.backup_and_reset_database()

            logger.info(f"🔌 Connecting to database at {self.db_url}")
            self.engine = create_async_engine(self.db_url, echo=False)
            self.session_factory = async_sessionmaker(
                self.engine, expire_on_commit=False
            )

            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ Database tables created/verified")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise

    async def close(self) -> None:
        """Close the database connection."""
        if self.engine:
            logger.info("🔌 Closing database connection")
            await self.engine.dispose()

    async def get_guild_settings(self, guild_id: int) -> GuildSettingsSchema:
        """Get guild settings, creating default if not exists."""
        if self.session_factory is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        async with self.session_factory() as session:
            result = await session.execute(
                select(GuildSettings).where(GuildSettings.guild_id == guild_id)
            )
            if not (guild_settings := result.scalar_one_or_none()):
                guild_settings = GuildSettings(guild_id=guild_id)
                session.add(guild_settings)
                await session.commit()
                await session.refresh(guild_settings)

            return GuildSettingsSchema.model_validate(guild_settings)

    async def update_guild_setting(
        self, guild_id: int, setting: str, value: Any
    ) -> None:
        """Update a specific guild setting."""
        update_data = GuildSettingUpdate(setting=setting, value=value)

        async with self.session_factory() as session:
            await session.execute(
                update(GuildSettings)
                .where(GuildSettings.guild_id == guild_id)
                .values(**{update_data.setting: update_data.value})
            )
            await session.commit()

    async def update_guild_settings_json(
        self, guild_id: int, settings_dict: dict[str, Any]
    ) -> None:
        """Update the JSON settings for a guild."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(GuildSettings).where(GuildSettings.guild_id == guild_id)
            )
            if not (guild_settings := result.scalar_one_or_none()):
                guild_settings = GuildSettings(guild_id=guild_id)
                session.add(guild_settings)
                await (
                    session.flush()
                )  # Ensure the object is persisted before setting attributes

            guild_settings.set_settings_dict(settings_dict)
            await session.commit()

    async def get_guild_settings_json(self, guild_id: int) -> GuildSettings | None:
        """Get the JSON settings for a guild."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(GuildSettings).where(GuildSettings.guild_id == guild_id)
            )
            if not (guild_settings := result.scalar_one_or_none()):
                return None

            return guild_settings

    async def is_feature_enabled(self, guild_id: int, feature: str) -> bool:
        """Check if a specific feature is enabled for a guild."""
        settings = await self.get_guild_settings(guild_id)
        return getattr(settings, feature, False)

    async def set_thread_model(self, guild_id: int, thread_id: int, model: str) -> None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(ThreadSettings).where(ThreadSettings.thread_id == thread_id)
            )
            if thread := result.scalar_one_or_none():
                thread.model = model
            else:
                thread = ThreadSettings(
                    thread_id=thread_id, guild_id=guild_id, model=model
                )
                session.add(thread)
            await session.commit()

    async def get_thread_model(self, thread_id: int) -> str | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(ThreadSettings).where(ThreadSettings.thread_id == thread_id)
            )
            if thread := result.scalar_one_or_none():
                return thread.model
            return None

    async def get_session(self) -> AsyncSession:
        """Get a database session."""
        if self.session_factory is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.session_factory()

    async def store_link_entry(
        self, guild_id: int, user_id: int, hostname: str, url: str
    ) -> None:
        """Store a link entry in the database."""
        async with self.session_factory() as session:
            link_entry = LinkEntry(
                guild_id=guild_id, user_id=user_id, hostname=hostname, url=url
            )
            session.add(link_entry)
            await session.commit()

    async def get_link_leaderboard(
        self, guild_id: int
    ) -> tuple[list[tuple[int, int]], list[tuple[str, int]], int] | None:
        """Get link leaderboard data for a guild."""
        async with self.session_factory() as session:
            user_query = (
                select(LinkEntry.user_id, func.count(LinkEntry.id).label("link_count"))
                .where(LinkEntry.guild_id == guild_id)
                .group_by(LinkEntry.user_id)
                .order_by(func.count(LinkEntry.id).desc())
                .limit(5)
            )

            if not (
                user_stats := [
                    (user_id, count)
                    for user_id, count in (await session.execute(user_query))
                ]
            ):
                user_stats = []

            domain_query = (
                select(LinkEntry.hostname, func.count(LinkEntry.id).label("link_count"))
                .where(LinkEntry.guild_id == guild_id)
                .group_by(LinkEntry.hostname)
                .order_by(func.count(LinkEntry.id).desc())
                .limit(5)
            )

            if not (
                domain_stats := [
                    (hostname, count)
                    for hostname, count in (await session.execute(domain_query))
                ]
            ):
                domain_stats = []

            total_query = select(func.count(LinkEntry.id)).where(
                LinkEntry.guild_id == guild_id
            )
            total_links = (await session.execute(total_query)).scalar() or 0

            if not user_stats and not domain_stats and total_links == 0:
                return None

            return user_stats, domain_stats, total_links

    async def get_user_link_stats(
        self, guild_id: int, user_id: int
    ) -> tuple[list[tuple[str, int]], int, int]:
        """Get link statistics for a specific user in a guild.

        Returns:
            Tuple containing:
            - List of (hostname, link_count) tuples for user's top domains
            - Total link count for the user
            - User's rank in the guild
        """
        async with self.session_factory() as session:
            # Get user's top domains
            domain_query = (
                select(LinkEntry.hostname, func.count(LinkEntry.id).label("link_count"))
                .where(LinkEntry.guild_id == guild_id, LinkEntry.user_id == user_id)
                .group_by(LinkEntry.hostname)
                .order_by(func.count(LinkEntry.id).desc())
                .limit(5)
            )

            domain_stats = [
                (hostname, count)
                for hostname, count in (await session.execute(domain_query))
            ]

            # Get total count for user
            total_query = select(func.count(LinkEntry.id)).where(
                LinkEntry.guild_id == guild_id, LinkEntry.user_id == user_id
            )
            total_links = (await session.execute(total_query)).scalar() or 0

            # Get user rank
            rank_query = (
                select(LinkEntry.user_id, func.count(LinkEntry.id).label("link_count"))
                .where(LinkEntry.guild_id == guild_id)
                .group_by(LinkEntry.user_id)
                .order_by(func.count(LinkEntry.id).desc())
            )

            all_users = [
                (uid, count) for uid, count in (await session.execute(rank_query))
            ]
            user_rank = next(
                (i + 1 for i, (uid, _) in enumerate(all_users) if uid == user_id), 0
            )

            return domain_stats, total_links, user_rank

    async def store_slap_entry(
        self, guild_id: int, slapper_id: int, slapped_id: int
    ) -> None:
        """Store a slap entry in the database."""
        async with self.session_factory() as session:
            slap_entry = SlapEntry(
                guild_id=guild_id, slapper_id=slapper_id, slapped_id=slapped_id
            )
            session.add(slap_entry)
            await session.commit()

    async def get_slap_leaderboard(
        self, guild_id: int
    ) -> tuple[list[tuple[int, int]], int] | None:
        """Get slap leaderboard data for a guild.

        Returns:
            Tuple containing:
            - List of (user_id, slap_count) tuples for users who got slapped the most
            - Total number of slaps in the guild
        """
        async with self.session_factory() as session:
            # Get users who got slapped the most
            slapped_query = (
                select(
                    SlapEntry.slapped_id, func.count(SlapEntry.id).label("slap_count")
                )
                .where(SlapEntry.guild_id == guild_id)
                .group_by(SlapEntry.slapped_id)
                .order_by(func.count(SlapEntry.id).desc())
                .limit(10)
            )

            slapped_stats = [
                (user_id, count)
                for user_id, count in (await session.execute(slapped_query))
            ]

            # Get total slaps count
            total_query = select(func.count(SlapEntry.id)).where(
                SlapEntry.guild_id == guild_id
            )
            total_slaps = (await session.execute(total_query)).scalar() or 0

            if not slapped_stats and total_slaps == 0:
                return None

            return slapped_stats, total_slaps

    async def get_user_slap_stats(
        self, guild_id: int, user_id: int
    ) -> tuple[int, int, int, int]:
        """Get slap statistics for a specific user in a guild.

        Returns:
            Tuple containing:
            - Number of times the user got slapped
            - Number of times the user slapped others
            - User's rank in getting slapped (1 = most slapped)
            - User's rank in slapping others (1 = most active slapper)
        """
        async with self.session_factory() as session:
            # Get times user got slapped
            slapped_count_query = select(func.count(SlapEntry.id)).where(
                SlapEntry.guild_id == guild_id, SlapEntry.slapped_id == user_id
            )
            times_slapped = (await session.execute(slapped_count_query)).scalar() or 0

            # Get times user slapped others
            slapper_count_query = select(func.count(SlapEntry.id)).where(
                SlapEntry.guild_id == guild_id, SlapEntry.slapper_id == user_id
            )
            times_slapping = (await session.execute(slapper_count_query)).scalar() or 0

            # Get user rank for getting slapped
            slapped_rank_query = (
                select(
                    SlapEntry.slapped_id, func.count(SlapEntry.id).label("slap_count")
                )
                .where(SlapEntry.guild_id == guild_id)
                .group_by(SlapEntry.slapped_id)
                .order_by(func.count(SlapEntry.id).desc())
            )

            all_slapped_users = [
                (uid, count)
                for uid, count in (await session.execute(slapped_rank_query))
            ]
            slapped_rank = next(
                (
                    i + 1
                    for i, (uid, _) in enumerate(all_slapped_users)
                    if uid == user_id
                ),
                0,
            )

            # Get user rank for slapping others
            slapper_rank_query = (
                select(
                    SlapEntry.slapper_id, func.count(SlapEntry.id).label("slap_count")
                )
                .where(SlapEntry.guild_id == guild_id)
                .group_by(SlapEntry.slapper_id)
                .order_by(func.count(SlapEntry.id).desc())
            )

            all_slapper_users = [
                (uid, count)
                for uid, count in (await session.execute(slapper_rank_query))
            ]
            slapper_rank = next(
                (
                    i + 1
                    for i, (uid, _) in enumerate(all_slapper_users)
                    if uid == user_id
                ),
                0,
            )

            return times_slapped, times_slapping, slapped_rank, slapper_rank


db = Database(db_url=os.getenv("DB_URL"))
