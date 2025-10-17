import logging
import os
import subprocess
import sys
from pathlib import Path

from discord.ext import commands
from discord import Intents

from app.config.app_settings import settings
from app.database import db
from app.utils.logger import setup_logging, get_logger

log_file = os.getenv("LOG_FILE", None)
setup_logging(
    level=settings.log_level,
    log_file=log_file,
    module_levels={
        "discord": logging.ERROR,
        "aiosqlite": logging.ERROR,
    },
)

logger = get_logger(__name__)


async def run_migrations():
    """Run Alembic migrations on startup."""
    try:
        # Get the project root directory (where alembic.ini is located)
        project_root = Path(__file__).parent.parent
        
        logger.info("🔄 Running database migrations...")
        
        # Run alembic upgrade head
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info("✅ Database migrations completed successfully")
        if result.stdout:
            logger.debug(f"Migration output: {result.stdout}")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Migration failed with exit code {e.returncode}")
        logger.error(f"Error output: {e.stderr}")
        logger.error(f"Standard output: {e.stdout}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error during migration: {e}")
        raise


class UncleRon(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=settings.prefix,
            description="Uncle Ron Bot",
            intents=Intents.all(),
        )

    async def setup_hook(self):
        """This runs before the bot is marked 'ready'."""
        # Run migrations first
        await run_migrations()
        
        await db.connect(reset_database=settings.reset_database)
        logger.info("🗄️ Database connected")

        for cog in settings.cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded {cog}")
            except Exception as e:
                logger.exception(f"❌ Failed to load cog: {cog} ({e})")

        await self.tree.sync()
        logger.info("🌍 Synced all slash commands")

    async def on_ready(self):
        logger.info(f"🤖 Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"📊 Connected to {len(self.guilds)} guilds")
        logger.info(f"👥 Serving {len(self.users)} users")

        for guild in self.guilds:
            logger.info(
                f"🏰 Guild: {guild.name} (ID: {guild.id}) - {guild.member_count} members"
            )

    async def on_guild_join(self, guild):
        logger.info(
            f"➕ Joined guild: {guild.name} (ID: {guild.id}) - {guild.member_count} members"
        )

    async def on_guild_remove(self, guild):
        logger.info(f"➖ Left guild: {guild.name} (ID: {guild.id})")

    async def on_command_error(self, ctx, error):
        logger.error(f"❌ Command error in {ctx.command}: {error}")
        await super().on_command_error(ctx, error)


def main():
    bot = UncleRon()
    logger.info("🚀 Starting Uncle Ron Bot")
    bot.run(token=settings.token, log_level=settings.log_level)


if __name__ == "__main__":
    main()
