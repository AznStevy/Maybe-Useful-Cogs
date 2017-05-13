import discord
from discord.ext import commands
from cogs.utils import checks
from discord.utils import find
from .utils.dataIO import fileIO

class Latex:
    """LaTeX."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, no_pm=True)
    async def latex(self, ctx, *, equation):
        """Takes a LaTeX expression and makes it pretty"""
        channel = ctx.message.channel
        user = ctx.message.author

        base_url = "http://latex.codecogs.com/gif.latex?%5Cbg_white%20%5CLARGE%20"
        url = "{}{}".format(base_url, equation)
        em = discord.Embed(description='', colour=user.colour)
        em.set_author(name="{}".format(equation), icon_url = user.avatar_url)
        em.set_image(url=url)
        await self.bot.say(embed = em)


def setup(bot):
    n = Latex(bot)
    bot.add_cog(n)