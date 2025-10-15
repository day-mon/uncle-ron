import discord
from discord.ext import commands
from urllib.parse import urlparse

from discord.ext.commands import Bot


class Twitter(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def _is_url(potential_url: str):
        try:
            return urlparse(potential_url)
        except Exception:
            return None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        url = self._is_url(message.content)
        if not url or url.hostname != "x.com":
            return

        fixed_url = message.content.split("?")[0].replace(url.hostname, "fixupx.com")

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="See on Twitter", url=message.content))

        await message.reply(
            content=f"{fixed_url}\n*Originally posted by {message.author.display_name}*",
            view=view,
            mention_author=False,
        )

        await message.delete()


async def setup(bot: Bot):
    await bot.add_cog(Twitter(bot))
