import discord
from discord.ext import commands
import random
import os
from .utils.dataIO import fileIO
from cogs.utils import checks

prefix = fileIO("data/red/settings.json", "load")['PREFIXES'][0]

class Markov:
    """A cog that generates text based on what your users say."""

    def __init__(self, bot):
        self.bot = bot
        self.model = fileIO("data/markov/model.json", "load")

    @commands.command(pass_context=True, no_pm=True)
    async def markov(self,ctx, *, msg = None):
        """This isn't the text you want."""

        user = ctx.message.author
        channel = ctx.message.channel
        server = user.server

        if not user.bot:
            if server.id not in self.model:
                self.model[server.id] = {}
            if channel.id not in self.model[server.id]:
                self.model[server.id][channel.id] = {}

            # generates sentence
            if msg == None:
                first_word = random.choice(list(self.model[server.id][channel.id].keys())) # first word
                markov_text = first_word + " "
                current_word = first_word
            else:
                first_word = msg.split(" ")[-1] # first word
                markov_text = msg + " "
                current_word = first_word

            while '?' not in markov_text and '\r' not in markov_text and '.' not in markov_text and prefix not in markov_text and len(markov_text) < 200:
                try:
                    new_word = random.choice(self.model[server.id][channel.id][current_word])
                    current_word = new_word
                    markov_text += new_word + " "
                except:
                    break

            await self.bot.say("**Generated Text: **{} ".format(markov_text))

    @commands.command(pass_context=True, no_pm=True)
    @checks.is_owner()
    async def clear(self,ctx):
        """Clears the data for specific channel."""
        user = ctx.message.author
        channel = ctx.message.channel
        server = user.server

        if server.id not in self.model:
            self.model[server.id] = {}
        if channel.id not in self.model[server.id]:
            self.model[server.id][channel.id] = {}

        self.model[server.id][channel.id] = {}
        fileIO('data/markov/model.json', "save", self.model)          
        await self.bot.say("Channel:`{}` data cleared.".format(channel.name))

    @commands.command(no_pm=True)
    async def size(self):
        """Shows the size of the file."""
        size = os.path.getsize('data/markov/model.json')
        await self.bot.say("Current File Size: `{}` Bytes.".format(size))        

    # loads the new text into the model
    async def track_message(self, message):
        text = message.content
        server = message.author.server
        channel = message.channel
        user = message.author

        if not user.bot and not text.startswith(prefix):
            words = text.split(" ")

            if server.id not in self.model:
                self.model[server.id] = {}
            if channel.id not in self.model[server.id]:
                self.model[server.id][channel.id] = {}

            for i in range(len(words) - 1):
                if words[i] not in self.model[server.id][channel.id]:
                    self.model[server.id][channel.id][words[i]] = list()
                self.model[server.id][channel.id][words[i]].append(words[i+1])

            fileIO('data/markov/model.json', "save", self.model)

# ------------------------------ setup ----------------------------------------    
def check_folders():
    if not os.path.exists("data/markov"):
        print("Creating data/markov folder...")
        os.makedirs("data/markov")

def check_files():
    f = "data/markov/model.json"
    if not fileIO(f, "check"):
        print("Creating model.json...")
        fileIO(f, "save", {})

def setup(bot):
    check_folders()
    check_files()

    n = Markov(bot)
    bot.add_listener(n.track_message,"on_message")
    bot.add_cog(n)
