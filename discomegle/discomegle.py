import discord
from discord.ext import commands
from __main__ import send_cmd_help
import aiohttp
from bs4 import BeautifulSoup
import random


class Konachan:
    """Gets images from Konachan."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True,no_pm=True)
    async def konachan(self, ctx, *text):
        """Retrieves a random result from Gelbooru
           Warning: Can and will display NSFW images"""
        server = ctx.message.server
        if len(text) > 0:
            msg = "+".join(text)
            search = "https://konachan.com/post?tags=" + msg
        else:
            search = "https://konachan.com/post?tags="
        url = await fetch_image(self, ctx, randomize=True, search=search)
        await self.bot.say(url)

def setup(bot):
    n = Konachan(bot)
    bot.add_cog(n)