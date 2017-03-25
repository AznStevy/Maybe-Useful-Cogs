import os
import discord
from discord.ext import commands
from .utils.dataIO import fileIO
import operator

class WhoPlays:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, no_pm=True)
    async def whoplays(self, ctx, *, game):
        """Shows a list of all the people playing a game."""
        if len(game) <= 2:
            await self.bot.say("You need at least 3 characters.")
            return     

        user = ctx.message.author
        server = ctx.message.server
        members = server.members

        playing_game = ""
        count_playing = 0
        for member in members:
            if member != None and member.game != None and member.game.name != None and not member.bot:
                if game.lower() in member.game.name.lower():
                    count_playing += 1
                    if count_playing <= 15:
                        playing_game += "▸ {} ({})\n".format(member.name, member.game.name)            

        if playing_game == "":
            await self.bot.say("No one is playing that game.")
        else:
            msg = playing_game
            em = discord.Embed(description=msg, colour=user.colour)
            if count_playing > 15:
                showing = "(Showing 15/{})".format(count_playing)
            else:
                showing = "({})".format(count_playing)                
            em.set_author(name="These are the people who are playing {} {}: \n".format(game, showing))
            await self.bot.say(embed = em)

    @commands.command(pass_context=True, no_pm=True)
    async def cgames(self, ctx):
        """Shows the currently most played games"""
        user = ctx.message.author
        server = ctx.message.server
        members = server.members

        freq_list = {}
        for member in members:
            if member != None and member.game != None and member.game.name != None and not member.bot:
                if member.game.name not in freq_list:
                    freq_list[member.game.name] = 0
                freq_list[member.game.name]+=1

        sorted_list = sorted(freq_list.items(), key=operator.itemgetter(1), reverse = True)    

        if not freq_list:
            await self.bot.say("Surprisingly, no one is playing anything.")
        else:            
            # create display
            msg = ""
            max_games = min(len(sorted_list), 10)
            for i in range(max_games):
                game, freq = sorted_list[i]
                msg+= "▸ {}: __{}__\n".format(game, freq_list[game])

            em = discord.Embed(description=msg, colour=user.colour)
            em.set_author(name="These are the server's most played games at the moment:")

            await self.bot.say(embed = em)         

def setup(bot):
    n = WhoPlays(bot)
    bot.add_cog(n)