import discord
from discord.ext import commands
import aiohttp
import asyncio
import random
from __main__ import send_cmd_help
from bs4 import BeautifulSoup
from .utils.dataIO import dataIO, fileIO

prefix = fileIO("data/red/settings.json", "load")['PREFIXES'][0]

class Discomegle:
    """Lets you chat with random person who has access to the bot."""

    def __init__(self, bot):
        self.bot = bot
        self.pool = {} # queue of users.id -> user channel
        self.link = {} # userid -> {target id, target user channel}

    @commands.command(pass_context=True, no_pm=True)
    async def discomegle(self, ctx):
        """Chat with other discord people anonymously!"""
        user = ctx.message.author
        channel = ctx.message.channel
        server = user.server

        msg = "```x1\n"
        msg += "In a private message to this bot: ```\n"   
        msg += "```x1\n"
        msg += prefix+"joinpool: Joins the pool\n"   
        msg += prefix+"next: Changes partners\n" 
        msg += prefix+"leavepool: Leaves the pool or conversation\n"  
        msg += prefix+"check: Checks who's there\n" 
        msg += "```" 
        await self.bot.say(msg)



    async def direct_message(self, message):
        msg = message.content
        user = message.author
        channel = message.channel

        if channel.is_private and not msg.startswith(prefix) and user.id in self.link:
            target_channel = self.link[user.id]["TARGET_CHANNEL"]
            await self.bot.send_message(target_channel, "**PARTNER: **{}".format(msg))
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
        await self.bot.send_message(channel, "**You have been added to the pool.**")  

    async def remove_from_pool(self, message):
        user = message.author
        channel =  message.channel

        if user.id in self.pool.keys():
            self.pool.pop(user.id)
            await self.bot.send_message(channel, "**Leaving discomegle pool.**")
        elif user.id in self.link.keys():
            # put partner back into pool
            partner_id = self.link[user.id]["TARGET_ID"]
            partner_channel = self.link[user.id]["TARGET_CHANNEL"]
            self.pool[partner_id] = partner_channel
            self.link.pop(partner_id)
            self.link.pop(user.id)
            await self.bot.send_message(partner_channel, "**Your partner has disconnected.**")
            await self.bot.send_message(channel, "**Leaving discomegle conversation and pool.**")
        else:
            await self.bot.send_message(channel, "**You are not in the pool or a conversation.**")            

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
            await self.bot.send_message(partner_channel, "**Your partner has disconnected.**")
            await self.bot.send_message(channel, "**Switching Users.**")
        elif user.id in self.pool.keys():
            await self.bot.send_message(channel, "**You're still in the pool. Please wait.**")
        else:
            await self.bot.send_message(channel, "**Your are not in the pool. Please do `{}joinpool`.**".format(prefix))                   

    async def get_info(self, message):
        channel =  message.channel

        msg = "```xl\n"
        msg += "Total Users: {}\n".format(len(self.pool) + len(self.link) )
        msg += "Users in conversation (should be even): {}\n".format(len(self.link))
        msg += "Unpaired users: {}".format(len(self.pool))
        msg += "```"
        await self.bot.send_message(channel, msg)


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
                await self.bot.send_message(user_one_channel, "**You have been paired. You can now start talking with your partner.**")   
                await self.bot.send_message(user_two_channel, "**You have been paired. You can now start talking with your partner.**")    
            await asyncio.sleep(5)

def setup(bot):
    n = Discomegle(bot)
    bot.add_listener(n.direct_message, 'on_message')
    bot.loop.create_task(n.create_link())
    bot.add_cog(n)