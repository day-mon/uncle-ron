from pathlib import Path
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select, update, text
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models.database import (
    Base,
    GuildSettings,
    GuildSettingsSchema,
    GuildSettingUpdate,
    ThreadSettings,
)
from app.models.links import LinkEntry
from sqlalchemy import select, func
from typing import List, Tuple, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class Database:
    def __init__(self, db_url: str | None = None):
        if db_url is None:
            base_dir = Path(__file__).resolve().parent
            db_url  = f"sqlite+aiosqlite:///{base_dir / 'guild_settings.db'}"
        self.db_url = db_url
        self.engine: Optional[create_async_engine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    async def connect(self):
        """Initialize database connection and create tables if they don't exist."""
        logger.info(f"🔌 Connecting to database at {self.db_url}")
        self.engine = create_async_engine(self.db_url, echo=False)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables created/verified")

    async def close(self):
        """Close the database connection."""
        if self.engine:
            logger.info("🔌 Closing database connection")
            await self.engine.dispose()

    async def get_guild_settings(self, guild_id: int) -> GuildSettingsSchema:
        """Get guild settings, creating default if not exists."""
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

    async def update_guild_setting(self, guild_id: int, setting: str, value: Any):
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
        self, guild_id: int, settings_dict: Dict[str, Any]
    ):
        """Update the JSON settings for a guild."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(GuildSettings).where(GuildSettings.guild_id == guild_id)
            )
            if not (guild_settings := result.scalar_one_or_none()):
                guild_settings = GuildSettings(guild_id=guild_id)
                session.add(guild_settings)

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

    async def set_thread_model(self, guild_id: int, thread_id: int, model: str):
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
            from app.models.database import ThreadSettings

            result = await session.execute(
                select(ThreadSettings).where(ThreadSettings.thread_id == thread_id)
            )
            if thread := result.scalar_one_or_none():
                return thread.model
            return None

    async def get_session(self) -> AsyncSession:
        """Get a database session."""
        return self.session_factory()
        
    async def store_link_entry(self, guild_id: int, user_id: int, hostname: str, url: str) -> None:
        """Store a link entry in the database."""
        async with self.session_factory() as session:
            link_entry = LinkEntry(
                guild_id=guild_id,
                user_id=user_id,
                hostname=hostname,
                url=url
            )
            session.add(link_entry)
            await session.commit()
            
    async def get_link_leaderboard(self, guild_id: int) -> Optional[Tuple[List[Tuple[int, int]], List[Tuple[str, int]], int]]:
        """Get link leaderboard data for a guild."""
        async with self.session_factory() as session:
            user_query = select(
                LinkEntry.user_id,
                func.count(LinkEntry.id).label("link_count")
            ).where(
                LinkEntry.guild_id == guild_id
            ).group_by(
                LinkEntry.user_id
            ).order_by(
                func.count(LinkEntry.id).desc()
            ).limit(5)
            
            if not (user_stats := [(user_id, count) for user_id, count in (await session.execute(user_query))]):
                user_stats = []
            
            domain_query = select(
                LinkEntry.hostname,
                func.count(LinkEntry.id).label("link_count")
            ).where(
                LinkEntry.guild_id == guild_id
            ).group_by(
                LinkEntry.hostname
            ).order_by(
                func.count(LinkEntry.id).desc()
            ).limit(5)
            
            if not (domain_stats := [(hostname, count) for hostname, count in (await session.execute(domain_query))]):
                domain_stats = []
            
            total_query = select(func.count(LinkEntry.id)).where(LinkEntry.guild_id == guild_id)
            total_links = (await session.execute(total_query)).scalar() or 0
            
            if not user_stats and not domain_stats and total_links == 0:
                return None
                
            return user_stats, domain_stats, total_links
            
    async def get_user_link_stats(self, guild_id: int, user_id: int) -> Tuple[List[Tuple[str, int]], int, int]:
        """Get link statistics for a specific user in a guild.
        
        Returns:
            Tuple containing:
            - List of (hostname, link_count) tuples for user's top domains
            - Total link count for the user
            - User's rank in the guild
        """
        async with self.session_factory() as session:
            # Get user's top domains
            domain_query = select(
                LinkEntry.hostname,
                func.count(LinkEntry.id).label("link_count")
            ).where(
                LinkEntry.guild_id == guild_id,
                LinkEntry.user_id == user_id
            ).group_by(
                LinkEntry.hostname
            ).order_by(
                func.count(LinkEntry.id).desc()
            ).limit(5)
            
            domain_stats = [(hostname, count) for hostname, count in (await session.execute(domain_query))]
            
            # Get total count for user
            total_query = select(func.count(LinkEntry.id)).where(
                LinkEntry.guild_id == guild_id,
                LinkEntry.user_id == user_id
            )
            total_links = (await session.execute(total_query)).scalar() or 0
            
            # Get user rank
            rank_query = select(
                LinkEntry.user_id,
                func.count(LinkEntry.id).label("link_count")
            ).where(
                LinkEntry.guild_id == guild_id
            ).group_by(
                LinkEntry.user_id
            ).order_by(
                func.count(LinkEntry.id).desc()
            )
            
            all_users = [(uid, count) for uid, count in (await session.execute(rank_query))]
            user_rank = next((i + 1 for i, (uid, _) in enumerate(all_users) if uid == user_id), 0)
            
            return domain_stats, total_links, user_rank


db = Database()
