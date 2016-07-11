import os
import discord
from discord.ext import commands
from .utils.dataIO import fileIO

class CurrGames:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, no_pm=True)
    async def playing(self, ctx, *, game:str):
        """Shows a list of all the members"""
        server = ctx.message.server
        members = server.members

        playing_game = ""
        for member in members:
            if member.game is not None:
                if member.game.name == game:
                    playing_game += "+ {}\n".format(member.name)

        if not playing_game:
            await self.bot.say("No one else is playing that game.")
        else:
            msg = "```python\n"
            msg += "These are the people who are playing {}: \n".format(game)
            msg += playing_game
            msg += "```"           
            await self.bot.say(msg)  

def setup(bot):
    n = CurrGames(bot)
    bot.add_cog(n)