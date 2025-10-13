import logging
import asyncio

from discord.ext import commands
from discord import Intents

from app.config.app_settings import settings
from app.database import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logging.getLogger("aiosqlite").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)


logger = logging.getLogger(__name__)


class UncleRon(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=settings.prefix,
            description="Uncle Ron Bot",
            intents=Intents.all(),
        )

    async def setup_hook(self):
        """This runs before the bot is marked 'ready'."""
        await db.connect()
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
    bot.run(token=settings.token, log_level=logging.ERROR)


if __name__ == "__main__":
    main()
