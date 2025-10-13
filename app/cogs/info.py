import platform
import psutil
import discord
from discord.ext.commands import Cog, Bot, hybrid_command
from datetime import datetime, timedelta


class Info(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @hybrid_command(name="host", description="Information about the host machine")
    async def host(self, ctx):
        os_name = platform.system()
        os_version = platform.version()
        os_release = platform.release()

        cpu = platform.processor()
        cpu_count = psutil.cpu_count(logical=True)

        mem = psutil.virtual_memory()
        total_mem = round(mem.total / (1024**3), 2)
        used_mem = round(mem.used / (1024**3), 2)

        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        uptime_str = str(timedelta(seconds=int(uptime.total_seconds())))

        embed = discord.Embed(
            title="💻 Host Machine Information", color=discord.Color.green()
        )

        embed.add_field(
            name="OS", value=f"{os_name} {os_release} ({os_version})", inline=False
        )
        embed.add_field(name="CPU", value=f"{cpu} ({cpu_count} cores)", inline=False)
        embed.add_field(
            name="Memory", value=f"{used_mem}GB / {total_mem}GB used", inline=False
        )
        embed.add_field(name="Uptime", value=uptime_str, inline=False)

        await ctx.send(embed=embed)


async def setup(bot: Bot):
    await bot.add_cog(Info(bot))
