import os
import discord
from discord.ext import commands
from discord.utils import find
from __main__ import send_cmd_help
import random, time
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
            "**No linked account**"
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
        self.num_best_plays = 5
        self.num_max_prof = 8
        self.max_map_disp = 3
        self.num_track_plays = 15

    @commands.group(pass_context=True)
    async def osuset(self, ctx):
        """Where you can define some settings"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            return

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
                osu_user = list(await get_user(key, username, 1))
                newuser = {
                    "discord_username": user.name, 
                    "osu_username": username,
                    "osu_user_id": osu_user[0]["user_id"],
                    "default_gamemode": 0,
                }

                self.user_settings[user.id] = newuser
                fileIO('data/osu/user_settings.json', "save", self.user_settings)
                await self.bot.say("{}, your account has been linked to osu! username `{}`".format(user.mention, osu_user[0]["username"]))
            except:
                await self.bot.say("{} doesn't exist in the osu! database.".format(username))
        else:
            try:
                osu_user = list(await get_user(key, username, 1))
                self.user_settings[user.id]["osu_username"] = username
                self.user_settings[user.id]["osu_user_id"] = osu_user[0]["user_id"]
                fileIO('data/osu/user_settings.json', "save", self.user_settings)
                await self.bot.say("{}, your osu! username has been edited to `{}`".format(user.mention, osu_user[0]["username"]))
            except:
                await self.bot.say("{} doesn't exist in the osu! database.".format(username))

    # Gets json information to proccess the small version of the image
    async def _process_user_info(self, ctx, usernames, gamemode: int):
        key = self.osu_api_key["osu_api_key"]
        channel = ctx.message.channel
        user = ctx.message.author
        server = user.server

        if not usernames:
            usernames = [None]

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
            userinfo = list(await get_user(key, final_usernames[i], gamemode)) # get user info from osu api
            if userinfo != None and len(userinfo) > 0:
                if "pp_rank" in userinfo[0] and userinfo[0]["pp_rank"] != None:
                    all_user_info.append(userinfo[0])
                    sequence.append((count_valid, int(userinfo[0]["pp_rank"])))
                    count_valid = count_valid + 1
            else:
                await self.bot.say("**{} has not played enough.**".format(final_usernames[i]))

        sequence = sorted(sequence, key=operator.itemgetter(1))

        all_players = []
        for i, pp in sequence:
            all_players.append(await self._get_user_info(user, all_user_info[i], gamemode))

        disp_num = min(self.num_max_prof, len(all_players))
        if disp_num < len(all_players):
            await self.bot.say("Found {} users, but displaying top {}.".format(len(all_players), disp_num))

        for player in all_players[0:disp_num]:
            try:
                await self.bot.say(embed=player)
            except:
                pass

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

        # gives the final input for osu username
        test_username = await self._process_username(ctx, username)
        if test_username:
            username = test_username
        else:
            return

        # get userinfo
        userinfo = list(await get_user(key, username, gamemode))
        userbest = list(await get_user_best(key, username, gamemode, self.num_best_plays))
        if userinfo and userbest:                          
            msg, top_plays = await self._get_user_top(user, userinfo[0], userbest, gamemode)
            await self.bot.say(msg)
            for play in top_plays:
                try:
                    await self.bot.say(embed=play)
                except:
                    pass
        else:
            await self.bot.say("**{} was not found or not enough plays** :cry:".format(username))

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
                if await get_user(key, username, 0):
                    username = str(target)
                else:
                    await self.bot.say(help_msg[2])
                    return
        # @ implies its a discord user (if not, it will just say user not found in the next section)
        # if not found, then oh well.
        elif "@" in username:   
            user_id = username.replace("@", "").replace("<","").replace(">","")
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

    async def _get_top_plays(self, user, userbest, gamemode:int):
        key = self.osu_api_key["osu_api_key"]

        # get best plays map information and scores
        best_beatmaps = []
        best_acc = []
        for i in range(self.num_best_plays):
            beatmap = list(await get_beatmap(key, beatmap_id=userbest[i]['beatmap_id']))[0]
            score = list(await get_scores(key, userbest[i]['beatmap_id'], user['user_id'], gamemode))[0]
            best_beatmaps.append(beatmap)
            best_acc.append(self.calculate_acc(score,gamemode))
        return best_beatmaps     

    # Gives a small user profile
    async def _get_user_info(self, server_user, user, gamemode: int):
        profile_url = 'http://s.ppy.sh/a/{}.png'.format(user['user_id'])
        flag_url = 'https://new.ppy.sh//images/flags/{}.png'.format(user['country']) 

        gamemode_text = self._get_gamemode(gamemode)

        try:
            user_url = 'https://osu.ppy.sh/u/' + user['user_id']
            em = discord.Embed(description='', colour=server_user.colour)
            em.set_author(name="{} Profile for {}".format(gamemode_text, user['username']), icon_url = flag_url, url = user_url)
            em.set_thumbnail(url=profile_url)

            info = ""
            info += "**▸ Global Rank:** *#{} (#{})*\n".format(user['pp_rank'], user['pp_country_rank'])
            info += "**▸ Total PP:** *{}*\n".format(user['pp_raw'])
            info += "**▸ Playcount:** *{}*\n".format(user['playcount'])
            info += "**▸ Hit Accuracy:** *{}%*".format(user['accuracy'][0:5])
            em.description = info
            return em 
        except:
            return None

    # Gives a user profile image with some information
    async def _get_user_top(self, server_user, user, userbest, gamemode:int):
        key = self.osu_api_key["osu_api_key"]

        profile_url = 'http://s.ppy.sh/a/{}.png'.format(user['user_id'])
        osu_logo_url = 'http://puu.sh/pT7JR/577b0cc30c.png'
        flag_url = 'https://new.ppy.sh//images/flags/{}.png'.format(user['country']) 

        gamemode_text = self._get_gamemode(gamemode)

        # get best plays map information and scores
        best_beatmaps = []
        best_acc = []
        for i in range(self.num_best_plays):
            beatmap = list(await get_beatmap(key, beatmap_id=userbest[i]['beatmap_id']))[0]
            score = list(await get_scores(key, userbest[i]['beatmap_id'], user['user_id'], gamemode))[0]
            best_beatmaps.append(beatmap)
            best_acc.append(self.calculate_acc(score,gamemode))

        num_plays = min(self.num_best_plays, 5)
        all_plays = []
        msg = "**Top {} {} Plays for {}:**".format(num_plays, gamemode_text, user['username'])

        for i in range(num_plays):
            info = ""
            info += "**▸ Accuracy:** {0:.2f}%\n".format(float(best_acc[i]))
            info += "**▸ PP: **{0:.2f}\n".format(float(userbest[i]['pp']))
            info += "**▸ Stars: **{0:.2f}★\n".format(float(best_beatmaps[i]['difficultyrating']))
            mods = self.mod_calculation(userbest[i]['enabled_mods'])
            if not mods:
                mods = []
                mods.append('No Mod')
            beatmap_url = 'https://osu.ppy.sh/b/' + best_beatmaps[i]['beatmap_id']

            # grab beatmap image
            page = urllib.request.urlopen(beatmap_url)
            soup = BeautifulSoup(page.read())
            map_image = [x['src'] for x in soup.findAll('img', {'class': 'bmt'})]
            map_image_url = 'http:{}'.format(map_image[0])

            em = discord.Embed(description=info, colour=server_user.colour)
            em.set_author(name="{}. {} [{}] +{} ({} Rank)".format(i+1, best_beatmaps[i]['title'], best_beatmaps[i]['version'], ",".join(mods),userbest[i]['rank']), url = beatmap_url)
            em.set_thumbnail(url=map_image_url)
            all_plays.append(em)

        return (msg, all_plays)

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
        mod_list =[]

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

    # ---------------------------- Detect Beatmaps ------------------------------
    # called by listener
    async def find_beatmap(self, message):
        if message.author.id == self.bot.user.id:
            return

        if 'https://osu.ppy.sh/s/' in message.content or 'https://osu.ppy.sh/b/' in message.content:
            await self.process_beatmap(message)

    # processes user input for the beatmap
    async def process_beatmap(self, message):
        key = self.osu_api_key["osu_api_key"]

        # process the the idea from a url in msg
        all_urls = []
        original_message = message.content
        while original_message.find('https://') != -1:
            url = re.search("(?P<url>https?://[^\s]+)", original_message).group("url")
            all_urls.append(url)
            original_message = original_message.replace(url, '')

        for url in all_urls:
            try:
                if url.find('https://osu.ppy.sh/s/') != -1:
                    beatmap_id = url.replace('https://osu.ppy.sh/s/','')
                    beatmap_info = await get_beatmapset(key, beatmap_id)
                elif url.find('https://osu.ppy.sh/b/') != -1:
                    beatmap_id = url.replace('https://osu.ppy.sh/b/','')
                    beatmap_info = await get_beatmap(key, beatmap_id)
                await self.disp_beatmap(message, beatmap_info, url)
            except:
                await self.bot.send_message(message.channel, "That beatmap doesn't exist.")   

    # displays the beatmap properly
    async def disp_beatmap(self, message, beatmap, beatmap_url:str):
        # process time
        num_disp = min(len(beatmap), self.max_map_disp)
        if (len(beatmap)>self.max_map_disp):
            await self.bot.send_message(message.channel, "Found {} maps, but only displaying {}.\n".format(len(beatmap), self.max_map_disp))            
        else:
            await self.bot.send_message(message.channel, "Found {} map(s).\n".format(len(beatmap)))

        beatmap_msg = ""
        m, s = divmod(int(beatmap[0]['total_length']), 60)
        tags = beatmap[0]['tags']
        if tags == "":
            tags = "-"
        desc = ' **Length:** {}m {}s  **BPM:** {}\n **Tags:** {}\n_-----------------_'.format(m, s, beatmap[0]['bpm'], tags)
        em = discord.Embed(description = desc, colour=0xeeeeee)
        em.set_author(name="{} - {}".format(beatmap[0]['title'], beatmap[0]['artist']), url=beatmap_url)

        # sort maps
        map_order = []
        for i in range(num_disp):
            map_order.append((i,float(beatmap[i]['difficultyrating'])))

        map_order = sorted(map_order, key=operator.itemgetter(1), reverse=True)

        for i, diff in map_order:
            beatmap_info = ""    
            beatmap_info += "**▸Difficulty:** {:.2f}★  **Max Combo:** {}\n".format(float(beatmap[i]['difficultyrating']), beatmap[i]['max_combo'])
            beatmap_info += "**▸AR:** {}  **▸OD:** {}  **▸HP:** {}  **▸CS:** {}\n".format(beatmap[i]['diff_approach'], beatmap[i]['diff_overall'], beatmap[i]['diff_drain'], beatmap[i]['diff_size'])
            em.add_field(name = "__[{}] by {}__\n".format(beatmap[i]['version'],beatmap[i]['creator']), value = beatmap_info)

        page = urllib.request.urlopen(beatmap_url)
        soup = BeautifulSoup(page.read())
        map_image = [x['src'] for x in soup.findAll('img', {'class': 'bmt'})]
        map_image_url = 'http:{}'.format(map_image[0]).replace(" ", "%")
        em.set_thumbnail(url=map_image_url)
        await self.bot.send_message(message.channel, embed = em)

    # --------------------- Tracking Section -------------------------------
    @osutrack.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def add(self, ctx, username:str, channel=None):
        """Adds a player to track for top scores."""
        if channel == None:
            channel = ctx.message.channel
        server = ctx.message.server

        key = self.osu_api_key["osu_api_key"]
        userinfo = list(await get_user(key, username, 0))
        if len(userinfo) == 0:
            await self.bot.say("{} does not exist in the osu! database.".format(username))
            return

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
                        user_plays[mode] = await get_user_best(key, username, self._get_gamemode_number(mode), self.num_track_plays)
                    self.track[username]["plays"] = user_plays

                    # add current userinfo
                    if "userinfo" not in self.track[username]:
                        self.track[username]["userinfo"] = {}
                    for mode in modes:
                        self.track[username]["userinfo"][mode] = list(await get_user(key, username, self._get_gamemode_number(mode)))[0]                    
                    await self.bot.say("**{} added. Will now track on #{}**".format(username, channel.name))
                    fileIO("data/osu/track.json", "save", self.track)
        else:
            if server.id in self.track[username]["servers"]:
                if channel.id == self.track[username]["servers"][server.id]["channel"]:
                    await self.bot.say("**Already tracking {} on #{}.**".format(username, channel.name))
                else:
                    self.track[username]["servers"][server.id]["channel"] = channel.id # add a channel to track
                    await self.bot.say("**{} now tracking on #{}**".format(username, channel.name))
                    fileIO("data/osu/track.json", "save", self.track)
            else:
                if server.id not in self.track[username]["servers"]:
                    self.track[username]["servers"][server.id] = {}
                self.track[username]["servers"][server.id]["channel"] = channel.id # add a channel to track
                await self.bot.say("**{} added. Will now track on #{}**".format(username, channel.name))
                fileIO("data/osu/track.json", "save", self.track)

    @osutrack.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def remove(self, ctx, username:str, channel=None):
        """Removes a player to track for top scores."""
        if channel == None:
            channel = ctx.message.channel
        server = ctx.message.server

        if username in self.track and "servers" in self.track[username] and server.id in self.track[username]["servers"]:
            if channel.id == self.track[username]["servers"][server.id]["channel"]:
                del self.track[username]["servers"][server.id]
                if len(self.track[username]["servers"].keys()) == 0:
                    del self.track[username]                  
                await self.bot.say("**No longer tracking {} in #{}.**".format(username, channel.name))
                fileIO("data/osu/track.json", "save", self.track)             
            else:
                await self.bot.say("**{} is not currently being tracked in #{}.**".format(username, channel.name))                 
        else:
            await self.bot.say("**{} is not currently being tracked.**".format(username))                

    # used to track top plays of specified users
    async def play_tracker(self):
        key = self.osu_api_key["osu_api_key"]
        while self == self.bot.get_cog('Osu'):

            # get all keys() to grab all current tracking users
            log.debug("looping through all users")
            for username in self.track.keys():
                log.debug("checking {}".format(username))
                # if the user's current top 10 scores are different from new top 10
                current_plays = self.track[username]["plays"]
                new_plays = {}
                new_plays["osu"] = await get_user_best(key, username, 0, self.num_track_plays)
                new_plays["taiko"] = await get_user_best(key, username, 1, self.num_track_plays)
                new_plays["ctb"] = await get_user_best(key, username, 2, self.num_track_plays)
                new_plays["mania"] = await get_user_best(key, username, 3, self.num_track_plays)

                # gamemode = word
                for gamemode in current_plays:
                    log.debug("examining gamemode {}".format(gamemode))
                    old_best = current_plays[gamemode]
                    new_best = new_plays[gamemode]
                    current_info = self.track[username]["userinfo"][gamemode]

                    if old_best != new_best:
                        log.debug("new score detected")
                        # loop to check what's different
                        for i in range(len(new_best)):
                            if i >= len(old_best) or old_best[i] != new_best[i]:
                                top_play_num = i+1
                                play = new_best[i]
                                play_map = await get_beatmap(key, new_best[i]['beatmap_id'])
                                new_user_info = list(await get_user(key, username, self._get_gamemode_number(gamemode)))
                                new_user_info = new_user_info[0]
                                # send appropriate message to channel

                                log.debug("creating top play")
                                em = self._create_top_play(top_play_num, play, play_map, self.track[username]["userinfo"][gamemode], new_user_info)
                                log.debug("sending embed")
                                for server_id in self.track[username]['servers'].keys():
                                    server = find(lambda m: m.id == server_id, self.bot.servers)                                    
                                    channel = find(lambda m: m.id == self.track[username]['servers'][server_id]["channel"], server.channels)
                                    await self.bot.send_message(channel, embed = em)
                        self.track[username]["plays"][gamemode] = new_best
                        fileIO("data/osu/track.json", "save", self.track)
                        break             

            log.debug("sleep 60 seconds")
            await asyncio.sleep(60)

    def _create_top_play(self, top_play_num, play, beatmap, old_user_info, new_user_info):
        beatmap_url = 'https://osu.ppy.sh/b/' + play['beatmap_id']
        user_url = 'https://osu.ppy.sh/u/' + new_user_info['user_id']
        profile_url = 'http://s.ppy.sh/a/{}.png'.format(new_user_info['user_id'])
        beatmap = beatmap[0]

        # get infomation
        log.debug("getting change information")
        dpp = float(new_user_info['pp_raw']) - float(old_user_info['pp_raw'])
        dgrank = float(new_user_info['pp_rank']) - float(old_user_info['pp_rank']) 
        dcrank = float(new_user_info['pp_country_rank']) - float(old_user_info['pp_country_rank'])
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
        info += "▸ +{} _**{:.2f}%**_ (**{}** Rank)\n".format(','.join(mods), float(acc), play['rank'])
        info += "▸ **{:.2f}★** ▸ {}:{} ▸ {}bpm\n".format(float(beatmap['difficultyrating']), m, s, beatmap['bpm'])
        info += "▸ {} ▸ x{} ▸ **{:.2f}pp**\n".format(play['score'], play['maxcombo'], float(play['pp']))
        info += "▸ #{} → #{} ({}#{} → #{})".format(old_user_info['pp_rank'], new_user_info['pp_rank'], old_user_info['country'], old_user_info['pp_country_rank'], old_user_info['pp_country_rank'])
        em.description = info
        return em

###-------------------------Python wrapper for osu! api-------------------------

# Gets the beatmap
async def get_beatmap(key, beatmap_id):
    url_params = []

    url_params.append(parameterize_key(key))
    url_params.append(parameterize_id("b", beatmap_id)) 

    async with aiohttp.ClientSession() as session:
        async with session.get(build_request(url_params, "https://osu.ppy.sh/api/get_beatmaps?")) as resp:
            return await resp.json()

# Gets the beatmap set
async def get_beatmapset(key, set_id):
    url_params = []

    url_params.append(parameterize_key(key))
    url_params.append(parameterize_id("s", set_id)) 

    async with aiohttp.ClientSession() as session:
        async with session.get(build_request(url_params, "https://osu.ppy.sh/api/get_beatmaps?")) as resp:
            return await resp.json()

# Grabs the scores
async def get_scores(key, beatmap_id, user_id, mode):
    url_params = []

    url_params.append(parameterize_key(key))
    url_params.append(parameterize_id("b", beatmap_id))   
    url_params.append(parameterize_id("u", user_id))
    url_params.append(parameterize_mode(mode))

    async with aiohttp.ClientSession() as session:
        async with session.get(build_request(url_params, "https://osu.ppy.sh/api/get_scores?")) as resp:
            return await resp.json()

async def get_user(key, user_id, mode): 
    url_params = []

    url_params.append(parameterize_key(key))
    url_params.append(parameterize_id("u", user_id))
    url_params.append(parameterize_mode(mode))

    async with aiohttp.ClientSession() as session:
        async with session.get(build_request(url_params, "https://osu.ppy.sh/api/get_user?")) as resp:
            return await resp.json()

async def get_user_best(key, user_id, mode, limit):
    url_params = []

    url_params.append(parameterize_key(key))
    url_params.append(parameterize_id("u", user_id))
    url_params.append(parameterize_mode(mode))
    url_params.append(parameterize_limit(limit)) 

    async with aiohttp.ClientSession() as session:
        async with session.get(build_request(url_params, "https://osu.ppy.sh/api/get_user_best?")) as resp:
            return await resp.json()

# Returns the user's ten most recent plays.
async def get_user_recent(key, user_id, mode, type):
    url_params = []

    url_params.append(parameterize_key(key))
    url_params.append(parameterize_id("u", user_id))
    url_params.append(parameterize_mode(mode)) 

    async with aiohttp.ClientSession() as session:
        async with session.get(build_request(url_params, "https://osu.ppy.sh/api/get_user_recent?")) as resp:
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
    elif (int(limit) >= 1 and int(limit) <= 50):
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

def setup(bot):
    check_folders()
    check_files()

    n = Osu(bot)
    loop = asyncio.get_event_loop()
    loop.create_task(n.play_tracker())
    bot.add_listener(n.find_beatmap, "on_message")    
    bot.add_cog(n)