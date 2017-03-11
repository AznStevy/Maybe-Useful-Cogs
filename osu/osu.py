import os
import discord
from discord.ext import commands
from discord.utils import find
from __main__ import send_cmd_help
import random, time, datetime
import aiohttp
import asyncio
import re, operator
import urllib.request
try:
    from bs4 import BeautifulSoup
except:
    raise RuntimeError("bs4 required: pip install beautifulsoup4")
from .utils.dataIO import fileIO
from cogs.utils import checks
import logging

prefix = fileIO("data/red/settings.json", "load")['PREFIXES'][0]
help_msg = [
            "**No linked account ({}osuset user) or not using **`{}command username gamemode`".format(prefix, prefix),
            "**No linked account ({}osuset user)**".format(prefix)
            ]

log = logging.getLogger("red.osu")
log.setLevel(logging.INFO)

class Osu:
    """Cog to give osu! stats for all gamemodes."""

    def __init__(self, bot):
        self.bot = bot
        self.osu_api_key = fileIO("data/osu/apikey.json", "load")
        self.user_settings = fileIO("data/osu/user_settings.json", "load")
        self.track = fileIO("data/osu/track.json", "load")
        self.osu_settings = fileIO("data/osu/osu_settings.json", "load")
        self.num_max_prof = 8
        self.max_map_disp = 3

    # ---------------------------- Settings ------------------------------------
    @commands.group(pass_context=True)
    async def osuset(self, ctx):
        """Where you can define some settings"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            return

    @osuset.command(pass_context=True, no_pm=True)
    @checks.is_owner()
    async def tracktop(self, ctx, top_num:int):
        """ Set # of top plays being tracked """
        msg = ""
        if top_num < 1 or top_num > 100:
            msg = "**Please enter a valid number. (1 - 100)**"
        else:
            self.osu_settings["num_track"] = top_num
            msg = "**Now tracking Top {} Plays.**".format(top_num)
            fileIO("data/osu/osu_settings.json", "save", self.osu_settings)
        await self.bot.say(msg)

    @osuset.command(pass_context=True, no_pm=True)
    @checks.is_owner()
    async def displaytop(self, ctx, top_num:int):
        """ Set # of best plays being displayed in top command """
        msg = ""
        if top_num < 1 or top_num > 10:
            msg = "**Please enter a valid number. (1 - 10)**"
        else:
            self.osu_settings["num_best_plays"] = top_num
            msg = "**Now Displaying Top {} Plays.**".format(top_num)
            fileIO("data/osu/osu_settings.json", "save", self.osu_settings)
        await self.bot.say(msg)  

    @osuset.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def tracking(self, ctx, toggle=None):
        """ For disabling tracking on server (enable/disable) """
        server = ctx.message.server

        if server.id not in self.osu_settings:
            self.osu_settings[server.id] = {}
            self.osu_settings[server.id]["tracking"] = True

        status = ""
        if not toggle:
            self.osu_settings[server.id]["tracking"] = not self.osu_settings[server.id]["tracking"]
            if self.osu_settings[server.id]["tracking"]:
                status = "Enabled"
            else:
                status = "Disabled"                
        elif toggle.lower() == "enable":
            self.osu_settings[server.id]["tracking"] = True
            status = "Enabled"
        elif toggle.lower() == "disable":
            self.osu_settings[server.id]["tracking"] = False
            status = "Disabled"
        fileIO("data/osu/osu_settings.json", "save", self.osu_settings)        
        await self.bot.say("**Player Tracking {} on {}.**".format(server.name, status))

    @osuset.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def overview(self, ctx):
        """ Get an overview of your settings """
        server = ctx.message.server
        user = ctx.message.author

        em = discord.Embed(description='', colour=user.colour)
        em.set_author(name="Current Settings for {}".format(server.name), icon_url = server.icon_url)

        # determine api to use
        try:
            if self.osu_settings[server.id]["api"] == self.osu_settings["type"]["official"]:
                api = "Official Osu! API"
            elif self.osu_settings[server.id]["api"] == self.osu_settings["type"]["ripple"]:
                api = "Ripple API"
        except: # catch all just in case..
            api = "Official Osu! API"

        # determine
        if server.id not in self.osu_settings or "tracking" not in self.osu_settings[server.id] or self.osu_settings[server.id]["tracking"] == True:                              
            tracking = "Enabled"
        else:
            tracking = "Disabled"

        info = ""
        info += "**▸ API:** {}\n".format(api)
        info += "**▸ Tracking:** {}\n".format(tracking)

        if tracking == "Enabled":
            info += "**▸ Tracking Number:** {}\n".format(self.osu_settings['num_track'])
        info += "**▸ Top Plays:** {}".format(self.osu_settings['num_best_plays'])        

        em.description = info
        await self.bot.say(embed = em)

    @osuset.command(pass_context=True, no_pm=True)
    @checks.is_owner()
    async def api(self, ctx, *, choice):
        """'official' or 'ripple'"""
        server = ctx.message.server
        if server.id not in self.osu_settings:
            self.osu_settings[server.id] = {}

        if not choice.lower() == "official" and not choice.lower() == "ripple":
            await self.bot.say("The two choices are `official` and `ripple`")
            return
        elif choice.lower() == "official":
            self.osu_settings[server.id]["api"] = self.osu_settings["type"]["default"]
        elif choice.lower() == "ripple":
            self.osu_settings[server.id]["api"] = self.osu_settings["type"]["ripple"]
        fileIO("data/osu/osu_settings.json", "save", self.osu_settings)
        await self.bot.say("**Switched to `{}` server on `{}`.**".format(choice, server.name))

    @osuset.command(pass_context=True, no_pm=True)
    async def default(self, ctx, mode:str):
        """ Set your default gamemode """
        user = ctx.message.author
        server = ctx.message.server

        modes = ["osu", "taiko", "ctb", "mania"]
        if mode.lower() in modes:
            gamemode = modes.index(mode.lower())
        elif int(mode) >= 0 & int(mode) <= 3:
            gamemode = int(mode)
        else:
            await self.bot.say("**Please enter a valid gamemode.**")
            return

        if user.id in self.user_settings:
            self.user_settings[user.id]['default_gamemode'] = gamemode
            await self.bot.say("**`{}`'s default gamemode has been set to `{}`.**".format(user.name, modes[gamemode]))
        else:
            await self.bot.say(help_msg[1])
            return
        fileIO('data/osu/user_settings.json', "save", self.user_settings)

    @commands.group(pass_context=True)
    async def osutrack(self, ctx):
        """Where you can define some settings"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            return 

    @osuset.command(pass_context=True)
    @checks.is_owner()
    async def key(self, ctx):
        """Sets your osu api key"""
        await self.bot.whisper("Type your osu! api key. You can reply here.")
        key = await self.bot.wait_for_message(timeout=30, author=ctx.message.author)
        if key is None:
            return
        else:
            self.osu_api_key["osu_api_key"] = key.content
            fileIO("data/osu/apikey.json", "save", self.osu_api_key)
            await self.bot.whisper("API Key details added.")

    @commands.command(pass_context=True, no_pm=True)
    async def osu(self, ctx, *username):
        """Gives osu user(s) stats."""
        await self._process_user_info(ctx, username, 0)

    @commands.command(pass_context=True, no_pm=True)
    async def osutop(self, ctx, *username):
        """Gives top osu plays."""
        await self._process_user_top(ctx, username, 0)

    @commands.command(pass_context=True, no_pm=True)
    async def taiko(self, ctx, *username):
        """Gives taiko user(s) stats."""
        await self._process_user_info(ctx, username, 1)

    @commands.command(pass_context=True, no_pm=True)
    async def taikotop(self, ctx, *username):
        """Gives top taiko plays."""
        await self._process_user_top(ctx, username, 1)

    @commands.command(pass_context=True, no_pm=True)
    async def ctb(self, ctx, *username):
        """Gives ctb user(s) stats."""
        await self._process_user_info(ctx, username, 2)

    @commands.command(pass_context=True, no_pm=True)
    async def ctbtop(self, ctx, *username):
        """Gives ctb osu plays."""
        await self._process_user_top(ctx, username, 2)

    @commands.command(pass_context=True, no_pm=True)
    async def mania(self, ctx, *username):
        """Gives mania user(s) stats."""
        await self._process_user_info(ctx, username, 3)

    @commands.command(pass_context=True, no_pm=True)
    async def maniatop(self, ctx, *username):
        """Gives top mania plays."""
        await self._process_user_top(ctx, username, 3)

    @commands.command(pass_context=True, no_pm=True)
    async def recent(self, ctx, *username):
        """Gives top mania plays."""
        await self._process_user_recent(ctx, username)

    @osuset.command(pass_context=True, no_pm=True)
    async def user(self, ctx, *, username):
        """Sets user information given an osu! username"""
        user = ctx.message.author
        channel = ctx.message.channel
        server = user.server
        key = self.osu_api_key["osu_api_key"]

        if user.server.id not in self.user_settings:
            self.user_settings[user.server.id] = {}

        if not self._check_user_exists(user):
            try:
                osu_user = list(await get_user(key, self.osu_settings["type"]["default"], username, 1))
                newuser = {
                    "discord_username": user.name, 
                    "osu_username": username,
                    "osu_user_id": osu_user[0]["user_id"],
                    "default_gamemode": 0,
                    "ripple_username": ""
                }

                self.user_settings[user.id] = newuser
                fileIO('data/osu/user_settings.json', "save", self.user_settings)
                await self.bot.say("{}, your account has been linked to osu! username `{}`".format(user.mention, osu_user[0]["username"]))
            except:
                await self.bot.say("{} doesn't exist in the osu! database.".format(username))
        else:
            try:
                osu_user = list(await get_user(key, self.osu_settings["type"]["default"], username, 1))
                self.user_settings[user.id]["osu_username"] = username
                self.user_settings[user.id]["osu_user_id"] = osu_user[0]["user_id"]
                fileIO('data/osu/user_settings.json', "save", self.user_settings)
                await self.bot.say("{}, your osu! username has been edited to `{}`".format(user.mention, osu_user[0]["username"]))
            except:
                await self.bot.say("{} doesn't exist in the osu! database.".format(username))

    # Gets json information to proccess the small version of the image
    async def _process_user_info(self, ctx, usernames, gamemode:int):
        key = self.osu_api_key["osu_api_key"]
        channel = ctx.message.channel
        user = ctx.message.author
        server = user.server

        if not usernames:
            usernames = [None]

        # get rid of duplicates
        usernames = list(set(usernames))

        # determine api to use
        try:
            if self.osu_settings[server.id]["api"] == self.osu_settings["type"]["official"]:
                api = self.osu_settings["type"]["default"]
            elif self.osu_settings[server.id]["api"] == self.osu_settings["type"]["ripple"]:
                api = self.osu_settings["type"]["ripple"]
        except: # catch all just in case..
            api = self.osu_settings["type"]["default"]

        # gives the final input for osu username
        final_usernames = []
        for username in usernames:
            test_username = await self._process_username(ctx, username)
            if test_username != None:
                final_usernames.append(test_username)

        # testing if username is osu username
        all_user_info = []
        sequence = []
        
        count_valid = 0
        for i in range(len(final_usernames)):
            userinfo = list(await get_user(key, api, final_usernames[i], gamemode)) # get user info from osu api
            if userinfo != None and len(userinfo) > 0:
                if "pp_rank" in userinfo[0] and userinfo[0]["pp_rank"] != None:
                    all_user_info.append(userinfo[0])
                    sequence.append((count_valid, int(userinfo[0]["pp_rank"])))
                    count_valid = count_valid + 1
            else:
                await self.bot.say("**`{}` has not played enough.**".format(final_usernames[i]))

        sequence = sorted(sequence, key=operator.itemgetter(1))

        all_players = []
        for i, pp in sequence:
            all_players.append(await self._get_user_info(api, server, user, all_user_info[i], gamemode))

        disp_num = min(self.num_max_prof, len(all_players))
        if disp_num < len(all_players):
            await self.bot.say("Found {} users, but displaying top {}.".format(len(all_players), disp_num))

        for player in all_players[0:disp_num]:
            try:
                await self.bot.say(embed=player)
            except:
                pass

    # Gets the user's most recent score
    async def _process_user_recent(self, ctx, username):
        key = self.osu_api_key["osu_api_key"]
        channel = ctx.message.channel
        user = ctx.message.author
        server = user.server

        if not username:
            username = None
        else:
            username = username[0]

        # determine api to use
        try:
            if self.osu_settings[server.id]["api"] == self.osu_settings["type"]["official"]:
                api = self.osu_settings["type"]["default"]
            elif self.osu_settings[server.id]["api"] == self.osu_settings["type"]["ripple"]:
                api = self.osu_settings["type"]["ripple"]
        except: # catch all just in case..
            api = self.osu_settings["type"]["default"]   

        # gives the final input for osu username
        test_username = await self._process_username(ctx, username)
        if test_username:
            username = test_username
        else:
            return

        # determine gamemode
        if self._check_user_exists(user):
            gamemode = self.user_settings[user.id]['default_gamemode']
        else:
            gamemode = 0

        # get userinfo
        userinfo = list(await get_user(key, api, username, gamemode))
        if not userinfo:
            await self.bot.say("**`{}` was not found or not enough plays** :cry:".format(username))
            return
        userinfo = userinfo[0]
        userrecent = list(await get_user_recent(key, api, username, gamemode))[0]
                         
        msg, recent_play = await self._get_recent(ctx, api, userinfo, userrecent, gamemode)
        await self.bot.say(msg, embed=recent_play)


    # Gets information to proccess the top play version of the image
    async def _process_user_top(self, ctx, username, gamemode: int):
        key = self.osu_api_key["osu_api_key"]
        channel = ctx.message.channel
        user = ctx.message.author
        server = user.server

        if not username:
            username = None
        else:
            username = username[0]

        # determine api to use
        try:
            if self.osu_settings[server.id]["api"] == self.osu_settings["type"]["official"]:
                api = self.osu_settings["type"]["default"]
            elif self.osu_settings[server.id]["api"] == self.osu_settings["type"]["ripple"]:
                api = self.osu_settings["type"]["ripple"]
        except: # catch all just in case..
            api = self.osu_settings["type"]["default"]

        # gives the final input for osu username
        test_username = await self._process_username(ctx, username)
        if test_username:
            username = test_username
        else:
            return

        # get userinfo
        userinfo = list(await get_user(key, api, username, gamemode))
        userbest = list(await get_user_best(key, api, username, gamemode, self.osu_settings['num_best_plays']))
        if userinfo and userbest:                          
            msg, top_plays = await self._get_user_top(ctx, api, userinfo[0], userbest, gamemode)
            await self.bot.say(msg, embed=top_plays)
        else:
            await self.bot.say("**`{}` was not found or not enough plays** :cry:".format(username))

    ## processes username. probably the worst chunck of code in this project so far. will fix/clean later
    async def _process_username(self, ctx, username):
        channel = ctx.message.channel
        user = ctx.message.author
        server = user.server
        key = self.osu_api_key["osu_api_key"]

        # if nothing is given, must rely on if there's account
        if not username:
            if self._check_user_exists(user):
                username = self.user_settings[user.id]["osu_username"]
            else:
                await self.bot.say("It doesn't seem that you have an account linked. Do **{}osuset user**.".format(prefix))
                return None # bad practice, but too lazy to make it nice
        # if it's a discord user, first check to see if they are in database and choose that username
        # then see if the discord username is a osu username, then try the string itself
        elif find(lambda m: m.name == username, channel.server.members) is not None:
            target = find(lambda m: m.name == username, channel.server.members)
            try:
                self._check_user_exists(target)
                username = self.user_settings[target.id]["osu_username"]
            except:
                if await get_user(key, self.osu_settings["type"]["default"], username, 0):
                    username = str(target)
                else:
                    await self.bot.say(help_msg[2])
                    return
        # @ implies its a discord user (if not, it will just say user not found in the next section)
        # if not found, then oh well.
        elif "@" in username:   
            user_id = username.replace("@", "").replace("<","").replace(">","").replace(prefix, "")
            try:
                if self.user_settings[user_id]:
                    username = self.user_settings[user_id]["osu_username"]
            except:
                await self.bot.say(help_msg[2])
                return
        else:
            username = str(username)

        return username

    # Checks if user exists
    def _check_user_exists(self, user):
        if user.id not in self.user_settings:
            return False
        return True

    # Gives a small user profile
    async def _get_user_info(self, api:str, server, server_user, user, gamemode: int):
        if api == self.osu_settings["type"]["default"]:
            profile_url ='http://s.ppy.sh/a/{}.png'.format(user['user_id'])
            pp_country_rank = " ({}#{})".format(user['country'], user['pp_country_rank'])
        elif api == self.osu_settings["type"]["ripple"]:
            profile_url = 'http://a.ripple.moe/{}.png'.format(user['user_id'])
            pp_country_rank = ""

        flag_url = 'https://new.ppy.sh//images/flags/{}.png'.format(user['country']) 

        gamemode_text = self._get_gamemode(gamemode)

        try:
            user_url = 'https://{}/u/{}'.format(api, user['user_id'])
            em = discord.Embed(description='', colour=server_user.colour)
            em.set_author(name="{} Profile for {}".format(gamemode_text, user['username']), icon_url = flag_url, url = user_url)
            em.set_thumbnail(url=profile_url)
            level_int = int(float(user['level']))       
            level_percent = float(user['level']) - level_int

            info = ""
            info += "**▸ Global Rank:** #{} {}\n".format(user['pp_rank'], pp_country_rank)
            info += "**▸ Level:** {} ({:.2f}%)\n".format(level_int, level_percent*100)            
            info += "**▸ Total PP:** {}\n".format(user['pp_raw'])
            info += "**▸ Playcount:** {}\n".format(user['playcount'])
            info += "**▸ Hit Accuracy:** {}%".format(user['accuracy'][0:5])
            em.description = info
            return em 
        except:
            return None

    async def _get_recent(self, ctx, api, user, userrecent, gamemode:int):
        server_user = ctx.message.author
        server = ctx.message.server
        key = self.osu_api_key["osu_api_key"]

        if api == self.osu_settings["type"]["default"]:
            profile_url = 'http://s.ppy.sh/a/{}.png'.format(user['user_id'])
        elif api == self.osu_settings["type"]["ripple"]:
            profile_url = 'http://a.ripple.moe/{}.png'.format(user['user_id'])

        flag_url = 'https://new.ppy.sh//images/flags/{}.png'.format(user['country']) 

        # get best plays map information and scores
        beatmap = list(await get_beatmap(key, api, beatmap_id=userrecent['beatmap_id']))[0]
        score = list(await get_scores(key, api, userrecent['beatmap_id'], user['user_id'], gamemode))
        if not score:
            return ("**No recent score for `{}` in user's default gamemode (`{}`)**".format(user['username'], self._get_gamemode(gamemode)), None)
        score = score[0]
        acc = self.calculate_acc(score, gamemode)
        mods = self.mod_calculation(userrecent['enabled_mods'])
        if not mods:
            mods = []
            mods.append('No Mod')
        beatmap_url = 'https://osu.ppy.sh/b/{}'.format(beatmap['beatmap_id'])

        msg = "**Most Recent {} Play for {}:**".format(self._get_gamemode(gamemode), user['username'])

        info = ""
        info += "▸ **Rank:** {} ▸ **Combo:** x{}\n".format(userrecent['rank'], userrecent['maxcombo'])
        info += "▸ **Score:** {} ▸ **Misses:** {}\n".format(userrecent['score'], userrecent['countmiss'])
        info += "▸ **Acc:** {:.2f}% ▸ **Stars:** {:.2f}★\n".format(float(acc), float(beatmap['difficultyrating']))

        # grab beatmap image
        page = urllib.request.urlopen(beatmap_url)
        soup = BeautifulSoup(page.read())
        map_image = [x['src'] for x in soup.findAll('img', {'class': 'bmt'})]
        map_image_url = 'http:{}'.format(map_image[0]).replace(" ","%")

        em = discord.Embed(description=info, colour=server_user.colour)
        em.set_author(name="{} [{}] +{}".format(beatmap['title'], beatmap['version'], ",".join(mods)), url = beatmap_url, icon_url = profile_url)
        em.set_thumbnail(url=map_image_url)
        em.set_footer(text = userrecent['date'])

        return (msg, em)

    # Gives a user profile image with some information
    async def _get_user_top(self, ctx, api, user, userbest, gamemode:int):
        server_user = ctx.message.author
        server = ctx.message.server
        key = self.osu_api_key["osu_api_key"]

        if api == self.osu_settings["type"]["default"]:
            profile_url = 'http://s.ppy.sh/a/{}.png'.format(user['user_id'])
        elif api == self.osu_settings["type"]["ripple"]:
            profile_url = 'http://a.ripple.moe/{}.png'.format(user['user_id'])

        gamemode_text = self._get_gamemode(gamemode)

        # get best plays map information and scores
        best_beatmaps = []
        best_acc = []
        for i in range(self.osu_settings['num_best_plays']):
            beatmap = list(await get_beatmap(key, api, beatmap_id=userbest[i]['beatmap_id']))[0]
            score = list(await get_scores(key, api, userbest[i]['beatmap_id'], user['user_id'], gamemode))[0]
            best_beatmaps.append(beatmap)
            best_acc.append(self.calculate_acc(score,gamemode))

        all_plays = []
        msg = "**Top {} {} Plays for {}:**".format(self.osu_settings['num_best_plays'], gamemode_text, user['username'])
        desc = ''
        for i in range(self.osu_settings['num_best_plays']):
            mods = self.mod_calculation(userbest[i]['enabled_mods'])
            if not mods:
                mods = []
                mods.append('No Mod')
            beatmap_url = 'https://osu.ppy.sh/b/{}'.format(best_beatmaps[i]['beatmap_id'])

            info = ''
            info += '***{}. [__{} [{}]__]({}) +{}\n***'.format(i+1, best_beatmaps[i]['title'], best_beatmaps[i]['version'], beatmap_url, ','.join(mods))
            info += '▸ **Rank:** {} ▸ **PP:** {:.2f}\n'.format(userbest[i]['rank'], float(userbest[i]['pp']))
            info += '▸ **Score:** {} ▸ **Combo:** x{}\n'.format(userbest[i]['score'], userbest[i]['maxcombo'])
            info += '▸ **Acc:** {:.2f}% ▸ **Stars:** {:.2f}★\n\n'.format(float(best_acc[i]), float(best_beatmaps[i]['difficultyrating']))
            desc += info
        em = discord.Embed(description=desc, colour=server_user.colour)
        em.set_thumbnail(url=profile_url)
        return (msg, em)

    def _get_gamemode(self, gamemode:int):
        if gamemode == 1:
            gamemode_text = "Taiko"
        elif gamemode == 2:
            gamemode_text = "Catch the Beat!"
        elif gamemode == 3:
            gamemode_text = "Osu! Mania"
        else:
            gamemode_text = "Osu! Standard"
        return gamemode_text

    def _get_gamemode_number(self, gamemode:str):
        if gamemode == "taiko":
            gamemode_text = 1
        elif gamemode == "ctb":
            gamemode_text = 2
        elif gamemode == "mania":
            gamemode_text = 3
        else:
            gamemode_text = 0
        return int(gamemode_text) 

    def calculate_acc(self, beatmap, gamemode:int):
        if gamemode == 0:
            total_unscale_score = float(beatmap['count300'])
            total_unscale_score += float(beatmap['count100']) 
            total_unscale_score += float(beatmap['count50']) 
            total_unscale_score += float(beatmap['countmiss'])
            total_unscale_score *=300
            user_score = float(beatmap['count300']) * 300.0
            user_score += float(beatmap['count100']) * 100.0
            user_score += float(beatmap['count50']) * 50.0
        elif gamemode == 1:
            total_unscale_score = float(beatmap['count300'])
            total_unscale_score += float(beatmap['count100'])
            total_unscale_score += float(beatmap['countmiss'])
            total_unscale_score *= 300
            user_score = float(beatmap['count300']) * 1.0
            user_score += float(beatmap['count100']) * 0.5
            user_score *= 300
        elif gamemode == 2:
            total_unscale_score = float(beatmap['count300'])
            total_unscale_score += float(beatmap['count100'])
            total_unscale_score += float(beatmap['count50'])
            total_unscale_score += float(beatmap['countmiss'])
            total_unscale_score += float(beatmap['countkatu'])
            user_score = float(beatmap['count300']) 
            user_score += float(beatmap['count100']) 
            user_score  += float(beatmap['count50'])
        elif gamemode == 3:
            total_unscale_score = float(beatmap['count300'])
            total_unscale_score += float(beatmap['countgeki']) 
            total_unscale_score += float(beatmap['countkatu']) 
            total_unscale_score += float(beatmap['count100'])  
            total_unscale_score += float(beatmap['count50']) 
            total_unscale_score += float(beatmap['countmiss']) 
            total_unscale_score *=300
            user_score = float(beatmap['count300']) * 300.0
            user_score += float(beatmap['countgeki']) * 300.0
            user_score += float(beatmap['countkatu']) * 200.0           
            user_score += float(beatmap['count100']) * 100.0            
            user_score += float(beatmap['count50']) * 50.0

        return (float(user_score)/float(total_unscale_score)) * 100.0

    # Truncates the text because some titles/versions are too long
    def truncate_text(self, text):
        if len(text) > 20:
            text = text[0:20] + '...'
        return text

    # gives a list of the ranked mods given a peppy number lol
    def mod_calculation(self, number):
        number = int(number)
        mod_list = []

        if number >= 16384:
            number -= 16384
            mod_list.append('PF')
        if number >= 4096:
            number-= 4096
            mod_list.append('SO')
        if number >= 1024:
            number-= 1024
            mod_list.append('FL')
        if number >= 576:
            number-= 576
            mod_list.append('NC')
        if number >= 256:
            number-= 256
            mod_list.append('HT')
        if number >= 128:
            number-= 128
            mod_list.append('RX')
        if number >= 64:
            number-= 64
            mod_list.append('DT')
        if number >= 32:
            number-= 32
            mod_list.append('SD')
        if number >= 16:
            number-= 16
            mod_list.append('HR')
        if number >= 8:
            number-= 8
            mod_list.append('HD')
        if number >= 2:
            number-= 2
            mod_list.append('EZ')
        if number >= 1:
            number-= 1
            mod_list.append('NF')
        return mod_list

    # ---------------------------- Detect Links ------------------------------
    # called by listener
    async def find_link(self, message):
        if message.author.id == self.bot.user.id:
            return

        if "https://" in message.content:
            # process the the idea from a url in msg
            all_urls = []
            original_message = message.content
            while original_message.find('https://') != -1:
                url = re.search("(?P<url>https?://[^\s]+)", original_message).group("url")
                all_urls.append(url)
                original_message = original_message.replace(url, '')

            # get rid of duplicates
            all_urls = list(set(all_urls))
            
            if 'https://osu.ppy.sh/u/' in message.content:
                await self.process_user_url(all_urls, message)

            if 'https://osu.ppy.sh/s/' in message.content or 'https://osu.ppy.sh/b/' in message.content:
                await self.process_beatmap(all_urls, message)

    # processes user input for user profile link
    async def process_user_url(self, all_urls, message):
        key = self.osu_api_key["osu_api_key"]
        server_user = message.author
        server = message.author.server

        for url in all_urls:
            try:
                if url.find('https://osu.ppy.sh/u/') != -1:
                    user_id = url.replace('https://osu.ppy.sh/u/','')
                    user_info = await get_user(key, self.osu_settings["type"]["default"], user_id, 0)
                    if user_id in self.user_settings:
                        gamemode = self.user_settings[user_id]["default_gamemode"]
                    else:
                        gamemode = 0
                    em = await self._get_user_info(self.osu_settings["type"]["default"], server, server_user, user_info[0], gamemode) 
                    await self.bot.send_message(message.channel, embed = em)                
            except:
                await self.bot.send_message(message.channel, "That user doesn't exist.")

    # processes user input for the beatmap
    async def process_beatmap(self, all_urls, message):
        key = self.osu_api_key["osu_api_key"]

        for url in all_urls:
            #try:
            if url.find('https://osu.ppy.sh/s/') != -1:
                beatmap_id = url.replace('https://osu.ppy.sh/s/','')
                beatmap_info = await get_beatmapset(key, self.osu_settings["type"]["default"], beatmap_id)
            elif url.find('https://osu.ppy.sh/b/') != -1:
                beatmap_id = url.replace('https://osu.ppy.sh/b/','')
                beatmap_info = await get_beatmap(key, self.osu_settings["type"]["default"], beatmap_id)
            await self.disp_beatmap(message, beatmap_info, url)
            #except:
                #await self.bot.send_message(message.channel, "That beatmap doesn't exist.")   

    # displays the beatmap properly
    async def disp_beatmap(self, message, beatmap, beatmap_url:str):
        # process time
        num_disp = min(len(beatmap), self.max_map_disp)
        if (len(beatmap)>self.max_map_disp):
            msg = "Found {} maps, but only displaying {}.\n".format(len(beatmap), self.max_map_disp)         
        else:
            msg = "Found {} map(s).\n".format(len(beatmap))

        beatmap_msg = ""
        m, s = divmod(int(beatmap[0]['total_length']), 60)
        tags = beatmap[0]['tags']
        if tags == "":
            tags = "-"
        desc = ' **Length:** {}:{}  **BPM:** {}\n **Tags:** {}\n_-----------------_'.format(m, str(s).zfill(2), beatmap[0]['bpm'], tags)
        em = discord.Embed(description = desc, colour=0xeeeeee)
        em.set_author(name="{} - {} by {}".format(beatmap[0]['title'], beatmap[0]['artist'], beatmap[0]['creator']), url=beatmap_url)

        # sort maps
        map_order = []
        for i in range(num_disp):
            map_order.append((i,float(beatmap[i]['difficultyrating'])))

        map_order = sorted(map_order, key=operator.itemgetter(1), reverse=True)

        for i, diff in map_order:
            beatmap_info = ""    
            beatmap_info += "**▸Difficulty:** {:.2f}★  **Max Combo:** {}\n".format(float(beatmap[i]['difficultyrating']), beatmap[i]['max_combo'])
            beatmap_info += "**▸AR:** {}  **▸OD:** {}  **▸HP:** {}  **▸CS:** {}\n".format(beatmap[i]['diff_approach'], beatmap[i]['diff_overall'], beatmap[i]['diff_drain'], beatmap[i]['diff_size'])
            em.add_field(name = "__[{}]__\n".format(beatmap[i]['version']), value = beatmap_info)

        page = urllib.request.urlopen(beatmap_url)
        soup = BeautifulSoup(page.read())
        map_image = [x['src'] for x in soup.findAll('img', {'class': 'bmt'})]
        map_image_url = 'http:{}'.format(map_image[0]).replace(" ", "%")
        # await self.bot.send_message(message.channel, map_image_url)        
        em.set_thumbnail(url=map_image_url)
        await self.bot.send_message(message.channel, msg, embed = em)

    # --------------------- Tracking Section -------------------------------
    @osutrack.command(pass_context=True, no_pm=True)
    async def list(self, ctx):
        """Check which players are currently tracked"""
        server = ctx.message.server
        channel = ctx.message.channel
        user = ctx.message.author

        em = discord.Embed(colour=user.colour)
        em.set_author(name="Osu! Players Currently Tracked in {}".format(server.name), icon_url = server.icon_url)
        channel_users = {}

        for username in self.track.keys():
            if server.id in self.track[username]["servers"]:
                target_channel = find(lambda m: m.id == self.track[username]['servers'][server.id]["channel"], server.channels)
                if target_channel.name not in channel_users:
                    channel_users[target_channel.name] = []
                channel_users[target_channel.name].append(username)

        channel_users[target_channel.name] = sorted(channel_users[target_channel.name])
        for channel_name in channel_users.keys():
            em.add_field(name = "__#{}__".format(channel_name), value = ", ".join(channel_users[channel_name]))
        await self.bot.say(embed = em)

    @osutrack.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def add(self, ctx, *usernames):
        """Adds a player to track for top scores."""
        server = ctx.message.server
        channel = ctx.message.channel

        key = self.osu_api_key["osu_api_key"]
        msg = ""

        if usernames == (None):
            await self.bot.say("Please enter a user")
            return

        for username in usernames:
            userinfo = list(await get_user(key, self.osu_settings["type"]["default"], username, 0))
            if len(userinfo) == 0:
                msg+="`{}` does not exist in the osu! database.\n".format(username)
            else:
                if username not in self.track:
                    self.track[username] = {}

                    if server.id not in self.track[username]:
                        self.track[username]["servers"] = {}
                        self.track[username]["servers"][server.id] = {}

                        # add channels that care about the user
                        if "channel" not in self.track[username]["servers"][server.id]:
                            self.track[username]["servers"][server.id]["channel"] = channel.id
                            # get top 10 plays
                            user_plays = {}
                            modes = ["osu", "taiko", "ctb", "mania"]
                            for mode in modes:
                                recent_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                                if "plays" not in self.track[username]:
                                    self.track[username]["plays"] = {}

                                self.track[username]["plays"][mode] = recent_time

                            # add current userinfo
                            if "userinfo" not in self.track[username]:
                                self.track[username]["userinfo"] = {}
                            for mode in modes:
                                self.track[username]["userinfo"][mode] = list(await get_user(key, self.osu_settings["type"]["default"], username, self._get_gamemode_number(mode)))[0]                    
                            msg+="**`{}` added. Will now track on `#{}`**\n".format(username, channel.name)
                            fileIO("data/osu/track.json", "save", self.track)
                else:
                    if server.id in self.track[username]["servers"]:
                        if channel.id == self.track[username]["servers"][server.id]["channel"]:
                            msg+="**Already tracking `{}` on `#{}.`**\n".format(username, channel.name)
                        else:
                            self.track[username]["servers"][server.id]["channel"] = channel.id # add a channel to track
                            msg+="**`{}` now tracking on `#{}`**\n".format(username, channel.name)
                            fileIO("data/osu/track.json", "save", self.track)
                    else:
                        if server.id not in self.track[username]["servers"]:
                            self.track[username]["servers"][server.id] = {}
                        self.track[username]["servers"][server.id]["channel"] = channel.id # add a channel to track
                        msg+="**`{}` added. Will now track on `#{}`**\n".format(username, channel.name)
                        fileIO("data/osu/track.json", "save", self.track)
        await self.bot.say(msg)

    @osutrack.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def remove(self, ctx, *usernames:str):
        """Removes a player to track for top scores."""
        server = ctx.message.server
        channel = ctx.message.channel
        msg = ""

        if usernames == (None):
            await self.bot.say("Please enter a user")
            return

        for username in usernames:
            if username in self.track and "servers" in self.track[username] and server.id in self.track[username]["servers"]:
                if channel.id == self.track[username]["servers"][server.id]["channel"]:
                    del self.track[username]["servers"][server.id]
                    if len(self.track[username]["servers"].keys()) == 0:
                        del self.track[username]                  
                    msg+="**No longer tracking `{}` in `#{}`.**\n".format(username, channel.name)
                    fileIO("data/osu/track.json", "save", self.track)             
                else:
                    msg+="**`{}` is not currently being tracked in `#{}`.**\n".format(username, channel.name)                
            else:
                msg+="**`{}` is not currently being tracked.**\n".format(username)
        await self.bot.say(msg)              

    # used to track top plays of specified users
    async def play_tracker(self):
        key = self.osu_api_key["osu_api_key"]
        while self == self.bot.get_cog('Osu'):

            # get all keys() to grab all current tracking users
            log.debug("looping through all users")
            for username in self.track.keys():
                log.debug("checking {}".format(username))
                # if the user's current top 10 scores are different from new top 10
                new_plays = {}
                modes = ["osu", "taiko", "ctb", "mania"]
                for mode in modes:
                    new_plays[mode] = await get_user_best(key, self.osu_settings["type"]["default"], username, self._get_gamemode_number(mode), self.osu_settings["num_track"])

                # gamemode = word
                for gamemode in self.track[username]["plays"].keys():
                    log.debug("examining gamemode {}".format(gamemode))
                    last_check = datetime.datetime.strptime(self.track[username]["plays"][gamemode], '%Y-%m-%d %H:%M:%S')
                    new_timestamps = []
                    for new_play in new_plays[gamemode]:
                        new_timestamps.append(datetime.datetime.strptime(new_play['date'], '%Y-%m-%d %H:%M:%S'))
                    current_info = self.track[username]["userinfo"][gamemode] # user information

                    # loop to check what's different
                    for i in range(len(new_timestamps)):
                        if last_check != None and new_timestamps[i] != None and new_timestamps[i] > last_check:
                            #print("Comparing new {} to old {}".format(new_timestamps[i], last_check))
                            top_play_num = i+1
                            play = new_plays[gamemode][i]
                            play_map = await get_beatmap(key, self.osu_settings["type"]["default"], play['beatmap_id'])
                            new_user_info = list(await get_user(key, self.osu_settings["type"]["default"], username, self._get_gamemode_number(gamemode)))
                            new_user_info = new_user_info[0]

                            # send appropriate message to channel
                            log.debug("creating top play")
                            if gamemode in self.track[username]["userinfo"]:
                                old_user_info = self.track[username]["userinfo"]
                                em = self._create_top_play(top_play_num, play, play_map, old_user_info[gamemode], new_user_info)
                            else:
                                old_user_info = None
                                em = self._create_top_play(top_play_num, play, play_map, old_user_info, new_user_info)
                                
                            log.debug("sending embed")
                            for server_id in self.track[username]['servers'].keys():
                                server = find(lambda m: m.id == server_id, self.bot.servers)
                                if server_id not in self.osu_settings or "tracking" not in self.osu_settings[server_id] or self.osu_settings[server_id]["tracking"] == True:
                                    channel = find(lambda m: m.id == self.track[username]['servers'][server_id]["channel"], server.channels)
                                    await self.bot.send_message(channel, embed = em)

                            #print("Setting last changed time to {}".format(new_timestamps[i]))                          
                            self.track[username]["plays"][gamemode] = new_timestamps[i].strftime('%Y-%m-%d %H:%M:%S')
                            self.track[username]["userinfo"][gamemode] = new_user_info
                            fileIO("data/osu/track.json", "save", self.track)
                            break

            try:
                log.debug("sleep 60 seconds")
                await asyncio.sleep(60)
            except:
                pass

    def _create_top_play(self, top_play_num, play, beatmap, old_user_info, new_user_info):
        beatmap_url = 'https://osu.ppy.sh/b/{}'.format(play['beatmap_id'])
        user_url = 'https://{}/u/{}'.format(self.osu_settings["type"]["default"], new_user_info['user_id'])
        profile_url = 'http://s.ppy.sh/a/{}.png'.format(new_user_info['user_id'])
        beatmap = beatmap[0]

        # get infomation
        log.debug("getting change information")
        m, s = divmod(int(beatmap['total_length']), 60)
        mods = self.mod_calculation(play['enabled_mods'])
        if not mods:
            mods = []
            mods.append('No Mod')
        em = discord.Embed(description='', colour=0xeeeeee)
        acc = self.calculate_acc(play, int(beatmap['mode']))

        # grab beatmap image
        log.debug("getting map image")
        page = urllib.request.urlopen(beatmap_url)
        soup = BeautifulSoup(page.read())
        map_image = [x['src'] for x in soup.findAll('img', {'class': 'bmt'})]
        map_image_url = 'http:{}'.format(map_image[0])
        em.set_thumbnail(url=map_image_url)
        log.debug("creating embed")
        em.set_author(name="New #{} for {} in {}".format(top_play_num, new_user_info['username'], self._get_gamemode(int(beatmap['mode']))), icon_url = profile_url, url = user_url)

        info = ""
        info += "▸ [{}[{}]]({})\n".format(beatmap['title'], beatmap['version'], beatmap_url)
        info += "▸ +{} ▸ **{:.2f}%** ▸ **{}** Rank\n".format(','.join(mods), float(acc), play['rank'])
        info += "▸ **{:.2f}★** ▸ {}:{} ▸ {}bpm\n".format(float(beatmap['difficultyrating']), m, str(s).zfill(2), beatmap['bpm'])
        if old_user_info != None:
            dpp = float(new_user_info['pp_raw']) - float(old_user_info['pp_raw'])
            info += "▸ {} ▸ x{} ▸ **{:.2f}pp (+{:.2f})**\n".format(play['score'], play['maxcombo'], float(play['pp']), dpp)
            info += "▸ #{} → #{} ({}#{} → #{})".format(old_user_info['pp_rank'], new_user_info['pp_rank'], new_user_info['country'], old_user_info['pp_country_rank'], new_user_info['pp_country_rank'])
        else:
            info += "▸ {} ▸ x{} ▸ **{:.2f}pp**\n".format(play['score'], play['maxcombo'], float(play['pp']))
            info += "▸ #{} ({}#{})".format(new_user_info['pp_rank'], new_user_info['country'], new_user_info['pp_country_rank'])
                
        em.description = info
        return em

###-------------------------Python wrapper for osu! api-------------------------

# Gets the beatmap
async def get_beatmap(key, api:str, beatmap_id):
    url_params = []

    url_params.append(parameterize_key(key))
    url_params.append(parameterize_id("b", beatmap_id)) 

    async with aiohttp.ClientSession() as session:
        async with session.get(build_request(url_params, "https://{}/api/get_beatmaps?".format(api))) as resp:
            return await resp.json()

# Gets the beatmap set
async def get_beatmapset(key, api:str, set_id):
    url_params = []

    url_params.append(parameterize_key(key))
    url_params.append(parameterize_id("s", set_id)) 

    async with aiohttp.ClientSession() as session:
        async with session.get(build_request(url_params, "https://{}/api/get_beatmaps?".format(api))) as resp:
            return await resp.json()

# Grabs the scores
async def get_scores(key, api:str, beatmap_id, user_id, mode):
    url_params = []

    url_params.append(parameterize_key(key))
    url_params.append(parameterize_id("b", beatmap_id))   
    url_params.append(parameterize_id("u", user_id))
    url_params.append(parameterize_mode(mode))

    async with aiohttp.ClientSession() as session:
        async with session.get(build_request(url_params, "https://{}/api/get_scores?".format(api))) as resp:
            return await resp.json()

async def get_user(key, api:str, user_id, mode): 
    url_params = []

    url_params.append(parameterize_key(key))
    url_params.append(parameterize_id("u", user_id))
    url_params.append(parameterize_mode(mode))

    async with aiohttp.ClientSession() as session:
        async with session.get(build_request(url_params, "https://{}/api/get_user?".format(api))) as resp:
            return await resp.json()

async def get_user_best(key, api:str, user_id, mode, limit):
    url_params = []

    url_params.append(parameterize_key(key))
    url_params.append(parameterize_id("u", user_id))
    url_params.append(parameterize_mode(mode))
    url_params.append(parameterize_limit(limit)) 

    async with aiohttp.ClientSession() as session:
        async with session.get(build_request(url_params, "https://{}/api/get_user_best?".format(api))) as resp:
            return await resp.json()

# Returns the user's ten most recent plays.
async def get_user_recent(key, api:str, user_id, mode):
    url_params = []

    url_params.append(parameterize_key(key))
    url_params.append(parameterize_id("u", user_id))
    url_params.append(parameterize_mode(mode)) 

    async with aiohttp.ClientSession() as session:
        async with session.get(build_request(url_params, "https://{}/api/get_user_recent?".format(api))) as resp:
            return await resp.json()

# Returns the full API request URL using the provided base URL and parameters.
def build_request(url_params, url):
    for param in url_params:
        url += str(param)
        if (param != ""):
            url += "&"
    return url[:-1]

def parameterize_event_days(event_days):
    if (event_days == ""):
        event_days = "event_days=1"
    elif (int(event_days) >= 1 and int(event_days) <= 31):
        event_days = "event_days=" + str(event_days)
    else:
        print("Invalid Event Days")
    return event_days

def parameterize_id(t, id):
    if (t != "b" and t != "s" and t != "u" and t != "mp"):
        print("Invalid Type")
    if (len(str(id)) != 0):
        return t + "=" + str(id)
    else:
        return ""

def parameterize_key(key):
    if (len(key) == 40):
        return "k=" + key
    else:
        print("Invalid Key")

def parameterize_limit(limit):
    ## Default case: 10 scores
    if (limit == ""):
        limit = "limit=10"
    elif (int(limit) >= 1 and int(limit) <= 100):
        limit = "limit=" + str(limit)
    else:
        print("Invalid Limit")
    return limit
  
def parameterize_mode(mode):
    ## Default case: 0 (osu!)
    if (mode == ""):
        mode = "m=0"
    elif (int(mode) >= 0 and int(mode) <= 3):
        mode = "m=" + str(mode)
    else:
        print("Invalid Mode")
    return mode  

###-------------------------Setup------------------------- 
def check_folders():
    if not os.path.exists("data/osu"):
        print("Creating data/osu folder...")
        os.makedirs("data/osu")

def check_files():
    osu_api_key = {"osu_api_key" : ""}
    api_file = "data/osu/apikey.json"

    if not fileIO(api_file, "check"):
        print("Adding data/osu/apikey.json...")
        fileIO(api_file, "save", osu_api_key)
    else:  # consistency check
        current = fileIO(api_file, "load")
        if current.keys() != osu_api_key.keys():
            for key in system.keys():
                if key not in osu_api_key.keys():
                    current[key] = osu_api_key[key]
                    print("Adding " + str(key) +
                          " field to osu apikey.json")
            fileIO(api_file, "save", current)

    # creates file for user backgrounds
    user_file = "data/osu/user_settings.json"
    if not fileIO(user_file, "check"):
        print("Adding data/osu/user_settings.json...")
        fileIO(user_file, "save", {})

    # creates file for player tracking
    user_file = "data/osu/track.json"
    if not fileIO(user_file, "check"):
        print("Adding data/osu/track.json...")
        fileIO(user_file, "save", {})
        
    # creates file for server to use
    settings_file = "data/osu/osu_settings.json"
    if not fileIO(settings_file, "check"):
        print("Adding data/osu/osu_settings.json...")
        fileIO(settings_file, "save", {
            "type": {
                "default": "osu.ppy.sh",
                "ripple":"ripple.moe"
                },
            "num_track" : 50,
            "num_best_plays": 5,
            })

def setup(bot):
    check_folders()
    check_files()

    n = Osu(bot)
    loop = asyncio.get_event_loop()
    loop.create_task(n.play_tracker())
    bot.add_listener(n.find_link, "on_message")    
    bot.add_cog(n)