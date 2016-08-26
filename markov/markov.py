import discord
from discord.ext import commands
import random
import os
from .utils.dataIO import dataIO
from cogs.utils import checks
from __main__ import send_cmd_help


class Markov:
    """A cog that generates text based on what your users say."""

    def __init__(self, bot):
        self.bot = bot
        self.model = dataIO.load_json("data/markov/model.json")
        self.settings = dataIO.load_json("data/markov/settings.json")

    def save_json(self):
        dataIO.save_json('data/markov/model.json', self.model)
        dataIO.save_json('data/markov/settings.json', self.settings)

    @commands.command(pass_context=True, no_pm=True)
    async def markov(self, ctx, *, msg=None):
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
            if msg is None:
                first_word = random.choice(list(self.model[server.id][channel.id].keys()))  # first word
                markov_text = first_word + " "
                current_word = first_word
            else:
                first_word = msg.split(" ")[-1]  # first word
                markov_text = msg + " "
                current_word = first_word

            bad_chars = ['?', '\r', '.'] + self.bot.command_prefix
            while not any(b in markov_text for b in bad_chars) and len(markov_text) < 200:
                try:
                    new_word = random.choice(self.model[server.id][channel.id][current_word])
                    current_word = new_word
                    markov_text += new_word + " "
                except:
                    break

            await self.bot.say("**Generated Text: **{} ".format(markov_text))

    @commands.group(pass_context=True, no_pm=True)
    async def mconf(self, ctx):
        """Configure markov cog"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @mconf.command(pass_context=True, no_pm=True, name='clear')
    @checks.is_owner()
    async def clear(self, ctx):
        """Clears the model for specific channel."""
        user = ctx.message.author
        channel = ctx.message.channel
        server = user.server

        if server.id not in self.model:
            self.model[server.id] = {}
        if channel.id not in self.model[server.id]:
            self.model[server.id][channel.id] = {}

        self.model[server.id][channel.id] = {}
        self.save_json()
        await self.bot.say("Channel:`{}` data cleared.".format(channel.name))

    @mconf.command(no_pm=True)
    @checks.is_owner()
    async def toggle(self, ctx, channel: discord.Channel = None):
        """Toggles markov generation for a certain channel (defaults to present)"""
        server = ctx.message.server
        channel = ctx.message.channel if channel else channel

        if server.id not in self.settings:
            self.settings[server.id] = {}
        if channel.id not in self.settings[server.id]:
            self.settings[server.id][channel.id] = False

        newval = not self.settings[server.id][channel.id]
        self.settings[server.id][channel.id] = newval

        verbs = ('disabled', 'enabled')
        await self.bot.say('Markov chain generation %s in %s' %
                           (verbs[int(newval)], channel.mention))
        self.save_json()

    @mconf.command(no_pm=True)
    @checks.is_owner()
    async def size(self):
        """Shows the size of the file."""
        size = os.path.getsize('data/markov/model.json')
        await self.bot.say("Current File Size: `{}` Bytes.".format(size))

    # loads the new text into the model
    async def track_message(self, message):
        try:
            text = message.content
            server = message.author.server
            channel = message.channel
            user = message.author

            if server.id not in self.settings:
                self.settings[server.id] = {}
            if channel.id not in self.settings[server.id]:
                self.settings[server.id][channel.id] = False

            if not self.settings[server.id][channel.id]:
                return

            if not user.bot and not any(text.startswith(p) for p in self.bot.command_prefix):
                words = text.split(" ")

                if server.id not in self.model:
                    self.model[server.id] = {}
                if channel.id not in self.model[server.id]:
                    self.model[server.id][channel.id] = {}

                for i in range(len(words) - 1):
                    if words[i] not in self.model[server.id][channel.id]:
                        self.model[server.id][channel.id][words[i]] = list()
                    self.model[server.id][channel.id][words[i]].append(words[i + 1])

                self.save_json()
        except:
            pass

# ------------------------------ setup ----------------------------------------


def check_folders():
    if not os.path.exists("data/markov"):
        print("Creating data/markov folder...")
        os.makedirs("data/markov")


def check_files():
    p = "data/markov/"
    for f in ['model.json', 'settings.json']:
        if not dataIO.is_valid_json(f):
            print("Creating %s..." % f)
            dataIO.save_json(p + f, {})


def setup(bot):
    check_folders()
    check_files()

    n = Markov(bot)
    bot.add_listener(n.track_message, "on_message")
    bot.add_cog(n)
