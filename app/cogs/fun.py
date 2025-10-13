import random
import discord
from discord.ext import commands
from discord import app_commands, Interaction
from discord.ext.commands import Cog, Bot


class Fun(Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def eight_ball_answers(self):
        return [
            "It is certain.",
            "It is decidedly so.",
            "You may rely on it.",
            "Without a doubt.",
            "Yes - definitely.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again later.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful.",
        ]

    @app_commands.command(name="praise", description="Praise the bot!")
    async def praise(self, interaction: Interaction):
        await interaction.response.send_message("OOF")

    @commands.hybrid_command(name="8ball", description="Ask the 8-ball a question")
    async def eight_ball(self, ctx: commands.Context, *, question: str):
        embed = discord.Embed(
            title="🎱 My Answer:",
            description=random.choice(self.eight_ball_answers),
            color=0xBEBEFE,
        )
        embed.set_footer(text=f"The question was: {question}")
        await ctx.send(embed=embed)


async def setup(bot: Bot):
    await bot.add_cog(Fun(bot))
