import discord
from discord.ext import commands
import aiohttp
import asyncio
import random
from __main__ import send_cmd_help
from .utils.dataIO import dataIO, fileIO

prefix = fileIO("data/red/settings.json", "load")['PREFIXES'][0]

class Discomegle:
    """Lets you chat with random person who has access to the bot."""

    def __init__(self, bot):
        self.bot = bot
        self.pool = {} # queue of users.id -> user channel
        self.link = {} # userid -> {target id, target user channel}
        self.colour = 0xAAAAAA

    @commands.command(pass_context=True, no_pm=True)
    async def discomegle(self, ctx):
        """Chat with other discord people anonymously!"""
        user = ctx.message.author
        channel = ctx.message.channel
        server = user.server

        msg = ""  
        msg += "▸ **{}joinpool**: Joins the pool\n".format(prefix)   
        msg += "▸ **{}next**: Changes partners\n".format(prefix) 
        msg += "▸ **{}leavepool**: Leaves the pool or conversation\n".format(prefix)   
        msg += "▸ **{}check**: Checks who's there\n".format(prefix)  

        em = discord.Embed(description=msg, colour=user.colour)
        em.set_author(name="In a private message to this bot:")
        await self.bot.say(embed = em)

    async def direct_message(self, message):
        msg = message.content
        user = message.author
        channel = message.channel

        if channel.is_private and not msg.startswith(prefix) and user.id in self.link:
            target_channel = self.link[user.id]["TARGET_CHANNEL"]
            em = discord.Embed(description=msg, colour=self.colour)
            em.set_author(name="Partner")
            await self.bot.send_message(target_channel, embed = em)

        else:
            if channel.is_private:
                if msg == (prefix + "joinpool"):
                    await self.add_to_pool(message)
                elif msg == (prefix + "leavepool"):
                    await self.remove_from_pool(message)
                elif msg == (prefix + "next"):
                    await self.get_next_user(message)
                elif msg == (prefix + "check"):
                    await self.get_info(message)

    async def add_to_pool(self, message):
        user = message.author
        channel =  message.channel
        self.pool[user.id] = channel

        em = discord.Embed(description="**You have been added to the pool.**", colour=self.colour)
        await self.bot.send_message(channel, embed = em)

    async def remove_from_pool(self, message):
        user = message.author
        channel =  message.channel

        if user.id in self.pool.keys():
            self.pool.pop(user.id)
            em = discord.Embed(description="**Leaving discomegle pool.**", colour=self.colour)
            await self.bot.send_message(channel, embed = em)
        elif user.id in self.link.keys():
            # put partner back into pool
            partner_id = self.link[user.id]["TARGET_ID"]
            partner_channel = self.link[user.id]["TARGET_CHANNEL"]
            self.pool[partner_id] = partner_channel
            self.link.pop(partner_id)
            self.link.pop(user.id)

            em = discord.Embed(description="**Your partner has disconnected.**", colour=self.colour)
            await self.bot.send_message(partner_channel, embed = em)

            em = discord.Embed(description="**You are not in the pool or a conversation.**", colour=self.colour)
            await self.bot.send_message(channel, embed = em)
        else:
            em = discord.Embed(description="**Leaving discomegle conversation and pool.**", colour=self.colour)
            await self.bot.send_message(channel, embed = em)           

    # puts both users back in the pool, but will go to same person if pool is small
    async def get_next_user(self, message):
        user = message.author
        channel =  message.channel
          
        if user.id in self.link.keys():
            # get partner information
            partner_id = self.link[user.id]["TARGET_ID"]
            partner_channel = self.link[user.id]["TARGET_CHANNEL"]
            self.pool[partner_id] = partner_channel
            self.pool[user.id] = channel
            
            self.link.pop(partner_id)
            self.link.pop(user.id)

            em = discord.Embed(description="**Your partner has disconnected.**", colour=self.colour)
            await self.bot.send_message(partner_channel, embed = em)

            em = discord.Embed(description="**Switching Users.**", colour=self.colour)
            await self.bot.send_message(channel, embed = em)

        elif user.id in self.pool.keys():
            em = discord.Embed(description="**You're still in the pool. Please wait.**", colour=self.colour)
            await self.bot.send_message(channel, embed = em)
        else:
            em = discord.Embed(description="**You are not in the pool. Please do `{}joinpool`.**", colour=self.colour)
            await self.bot.send_message(channel, embed = em)                 

    async def get_info(self, message):
        channel =  message.channel

        msg = ""
        msg += "▸ Total Users: __{}__\n".format(len(self.pool) + len(self.link) )
        msg += "▸ Users in conversation (should be even): __{}__\n".format(len(self.link))
        msg += "▸ Unpaired users: __{}__".format(len(self.pool))

        em = discord.Embed(description=msg, colour=self.colour)
        await self.bot.send_message(channel, embed = em) 

    async def create_link(self):
        while self == self.bot.get_cog('Discomegle'):
            if len(self.pool) >= 2:
                # get two users
                user_one_id = random.choice(list(self.pool.keys()))
                user_one_channel = self.pool[user_one_id]
                self.pool.pop(user_one_id, None)

                user_two_id = random.choice(list(self.pool.keys()))
                user_two_channel = self.pool[user_two_id]
                self.pool.pop(user_two_id, None)

                self.link[user_one_id] = {"TARGET_ID": user_two_id, "TARGET_CHANNEL": user_two_channel}
                self.link[user_two_id] = {"TARGET_ID": user_one_id, "TARGET_CHANNEL": user_one_channel}

                em = discord.Embed(description="**You have been paired. You can now start talking with your partner.**", colour=self.colour)
                await self.bot.send_message(user_one_channel, embed = em)  

                em = discord.Embed(description="**You have been paired. You can now start talking with your partner.**", colour=self.colour)
                await self.bot.send_message(user_two_channel, embed = em)  

            await asyncio.sleep(5)

def setup(bot):
    n = Discomegle(bot)
    bot.add_listener(n.direct_message, 'on_message')
    bot.loop.create_task(n.create_link())
    bot.add_cog(n)