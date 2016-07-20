import os
import discord
from discord.ext import commands
from discord.utils import find
from __main__ import send_cmd_help
import random
import aiohttp
from .utils.dataIO import fileIO
from wand.image import Image
from wand.display import display
from wand.drawing import Drawing
from wand.color import Color
from cogs.utils import checks

bgs = {
    'blue_triangles':'http://puu.sh/pUeKt/bd02db94a1.jpg',
    'rainbow_circles': 'http://puu.sh/pUdMe/4cdc33ed08.jpg',
    'blue_triangles_2': 'http://puu.sh/pVjqw/06b6b6395f.jpg',
    'blue_triangles_3': 'http://puu.sh/pUdJb/47220936c9.jpg',
    'purple_orange_pentagons': 'http://puu.sh/pUdBf/8959a98929.png',
    'pink_white_triangles': 'http://puu.sh/pUdyQ/62eee8b326.jpg',
    'purple_pink_triangles': 'http://puu.sh/pSSFN/34704f54e7.jpg,',
    'waterfall': 'http://puu.sh/pSSHJ/20fd045df0.jpg',
    'pink_triangles': 'http://puu.sh/pST3z/238863993a.png',
    'rainbow_triangles': 'http://puu.sh/pST4a/563337774d.jpg',
    'blue_green_triangles': 'http://puu.sh/pWfYt/f3099aa970.jpg',
    'random': 'A random bg from this list'
}

prefix = fileIO("data/red/settings.json", "load")['PREFIXES'][0]
help_msg = [
            "That player either doesn't exist in the database, hasn't played enough, or the owner hasn't set an osu api key (*it's required*). You can get one from https://osu.ppy.sh/p/api. If already have a key, do **{}osuset key** to set your key".format(prefix),
            "It doesn't seem that you have an account linked. Do **{}osuset user**.".format(prefix),
            "It doesn't seem that the discord user has an account linked."
            ]

class Osu:
    """Cog to give osu! stats for all gamemodes."""

    def __init__(self, bot):
        self.bot = bot
        self.osu_api_key = fileIO("data/osu/apikey.json", "load")
        self.user_settings = fileIO("data/osu/user_settings.json", "load")

    @commands.group(pass_context=True)
    async def osuset(self, ctx):
        """Where you can define some settings"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            return 

    @osuset.command(pass_context=True)
    @checks.is_owner()
    async def key(self, ctx):
        """Sets your osu api key"""
        await self.bot.whisper("Type your osu! api key. You can reply here.")
        key = await self.bot.wait_for_message(timeout=30,
                                                   author=ctx.message.author)
        if key is None:
            return
        else:
            self.osu_api_key["osu_api_key"] = key.content
            fileIO("data/osu/apikey.json", "save", self.osu_api_key)
            await self.bot.whisper("API Key details added.")

    @commands.command(pass_context=True, no_pm=True)
    async def osu(self, ctx, *, username= None):
        """Gives osu! standard user stats"""
        await self.process_user_small(ctx, username, 0)

    @commands.command(pass_context=True, no_pm=True)
    async def taiko(self, ctx, *, username=None):
        """Gives taiko user stats"""
        await self.process_user_small(ctx, username, 1)

    @commands.command(pass_context=True, no_pm=True)
    async def ctb(self, ctx, *, username=None):
        """Gives Catch the Beat user stats"""
        await self.process_user_small(ctx, username, 2)

    @commands.command(pass_context=True, no_pm=True)
    async def mania(self, ctx, *, username=None):
        """Gives osu standard user stats"""
        await self.process_user_small(ctx, username, 3)

    @commands.command(pass_context=True, no_pm=True)
    async def osutop(self, ctx, *, username=None):
        """Gives osu! standard user best plays"""
        await self.process_user_profile(ctx, username, 0)

    @commands.command(pass_context=True, no_pm=True)
    async def taikotop(self, ctx, *, username=None):
        """Gives taiko user stats and best plays"""
        key = self.osu_api_key["osu_api_key"]
        await self.process_user_profile(ctx, username, 1)

    @commands.command(pass_context=True, no_pm=True)
    async def ctbtop(self, ctx, *, username=None):
        """Gives ctb user stats and best plays"""
        key = self.osu_api_key["osu_api_key"]
        await self.process_user_profile(ctx, username, 2)

    @commands.command(pass_context=True, no_pm=True)
    async def maniatop(self, ctx, *, username=None):
        """Gives osu! mania user stats and best plays"""
        key = self.osu_api_key["osu_api_key"]
        await self.process_user_profile(ctx, username, 3)

    @osuset.command(pass_context=True, no_pm=True)
    async def listbgs(self, ctx):
        """Ugly list of available backgrounds. Will fix."""
        await self.bot.say("Here is a list of the current available backgrounds:\n")
        bg_list = "```"
        for background in bgs.keys():
            bg_list += "{:>24}  <{:>24}> \n".format(background, bgs[background])
        bg_list += "```"
        await self.bot.say(bg_list)
        await self.bot.say("If you would like to set a default background, do **{}osuset bg**".format(prefix))

    @osuset.command(pass_context=True, no_pm=True)
    async def user(self, ctx, *, username):
        """Sets user information given an osu! username"""
        user = ctx.message.author
        channel = ctx.message.channel
        server = user.server
        key = self.osu_api_key["osu_api_key"]

        if user.server.id not in self.user_settings:
            self.user_settings[user.server.id] = {}

        if not self.check_user_exists(user):
            try:
                osu_user = list(await get_user(key, username, 1))
                newuser = {
                    "discord_username": user.name, 
                    "osu_username": username,
                    "osu_user_id": osu_user[0]["user_id"],
                    "default_gamemode": 0,
                    "background": ""
                }

                self.user_settings[server.id][user.id] = newuser
                fileIO('data/osu/user_settings.json', "save", self.user_settings)
                await self.bot.say("{}, your account has been linked to osu! username `{}`".format(user.mention, osu_user[0]["username"]))
            except:
                await self.bot.say("{} doesn't exist in the osu! database.".format(username))
        else:
            try:
                osu_user = list(await get_user(key, username, 1))
                self.user_settings[server.id][user.id]["osu_username"] = username
                self.user_settings[server.id][user.id]["osu_user_id"] = osu_user[0]["user_id"]
                fileIO('data/osu/user_settings.json', "save", self.user_settings)
                await self.bot.say("{}, your osu! username has been edited to `{}`".format(user.mention, osu_user[0]["username"]))
            except:
                await self.bot.say("{} doesn't exist in the osu! database.".format(username))
                         
    @osuset.command(pass_context=True, no_pm=True)
    async def bg(self, ctx, background_name):
        """Sets user background"""
        user = ctx.message.author
        server = user.server
        channel = ctx.message.channel

        if self.check_user_exists(user):
            if background_name in bgs.keys():
                self.user_settings[server.id][user.id]["background"] = background_name
                await self.bot.say("{}, your default background is now: `{}`".format(user.mention, background_name))            
            else:
                await self.bot.say("That is not a valid background. Do **{}osuset listbgs** to view a list.".format(prefix))          
        else:
            await self.bot.say(help_msg[1])  

    # Gets json information to proccess the small version of the image
    async def process_user_small(self, ctx, username, gamemode: int):
        key = self.osu_api_key["osu_api_key"]
        channel = ctx.message.channel
        user = ctx.message.author
        server = user.server

        if await self.process_username(ctx, username):
            username = await self.process_username(ctx, username)
        else:
            return

        try: 
            userinfo = list(await get_user(key, username, gamemode))
            if userinfo:
                if self.check_user_exists(user):
                    if username == self.user_settings[server.id][user.id]["osu_username"]:
                        await self.draw_user_small(userinfo[0], gamemode, self.user_settings[server.id][user.id]["background"])
                    else:
                        await self.draw_user_small(userinfo[0], gamemode, "") # random background
                else:
                    await self.draw_user_small(userinfo[0], gamemode, "") # random background
                
                await self.bot.send_typing(channel)            
                await self.bot.send_file(channel, 'data/osu/user.png')
            else:
                await self.bot.say("Player not found :cry:")
        except:
            await self.bot.say(help_msg[0])

    # Gets json information to proccess the top play version of the image
    async def process_user_profile(self, ctx, username, gamemode: int):
        key = self.osu_api_key["osu_api_key"]
        channel = ctx.message.channel
        user = ctx.message.author
        server = user.server
        num_best_plays = 5 # edit for more plays

        if await self.process_username(ctx, username):
            username = await self.process_username(ctx, username)
        else:
            return

        try:
            # get userinfo
            userinfo = list(await get_user(key, username, gamemode))
            userbest = list(await get_user_best(key, username, gamemode, num_best_plays))
            if userinfo:
                if self.check_user_exists(user):
                    if username == self.user_settings[server.id][user.id]["osu_username"]:
                        await self.draw_user_profile(userinfo[0], userbest, gamemode, self.user_settings[server.id][user.id]["background"]) # only takes the first one
                    else:
                        await self.draw_user_profile(userinfo[0],userbest, gamemode, "") # random background                            
                else:
                    await self.draw_user_profile(userinfo[0],userbest, gamemode, "") # random background                            
                await self.bot.send_typing(channel)
                await self.bot.send_file(channel, 'data/osu/user_profile.png')
            else:
                await self.bot.say("Player not found :cry:")
        except:
            await self.bot.say(help_msg[0])

    ## processes username. probably the worst chunck of code in this project so far. will fix/clean later
    async def process_username(self, ctx, username):
        channel = ctx.message.channel
        user = ctx.message.author
        server = user.server
        key = self.osu_api_key["osu_api_key"]

        # if nothing is given, must rely on if there's account
        if not username:
            if self.check_user_exists(user):
                username = self.user_settings[server.id][user.id]["osu_username"]
            else:
                await self.bot.say("It doesn't seem that you have an account linked. Do **{}osuset user**.".format(prefix))
                return # bad practice, but too lazy to make it nice
        # if it's a discord user, first check to see if they are in database and choose that username
        # then see if the discord username is a osu username, then try the string itself
        elif find(lambda m: m.name == username, channel.server.members) is not None:
            target = find(lambda m: m.name == username, channel.server.members)
            try:
                self.check_user_exists(target)
                username = self.user_settings[server.id][target.id]["osu_username"]
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
                if self.user_settings[server.id][user_id]:
                    username = self.user_settings[server.id][user_id]["osu_username"]
            except:
                await self.bot.say(help_msg[2])
                return
        else:
            username = str(username)
        return username

    # Checks if user exists
    def check_user_exists(self, user):
        if user.server.id not in self.user_settings:
            self.user_settings[user.server.id] = {}

        if user.id not in self.user_settings[user.server.id]:
            return False
        return True

    # Gives a small user profile image
    async def draw_user_small(self, user, gamemode: int, background:str):
        font = 'Tahoma'

        # get urls
        if background in bgs.keys() and background != 'random':
            bg_url = bgs[background]
        else:
            bg_url = random.choice(list(bgs.values()))  
        profile_url = 'http://s.ppy.sh/a/{}.png'.format(user['user_id'])
        osu_logo_url = 'http://puu.sh/pT7JR/577b0cc30c.png'
        icons_url=['http://puu.sh/pT2wd/4009301880.png','http://puu.sh/pT7XO/04a636cd31.png', 'http://puu.sh/pT6L5/3528ea348a.png','http://puu.sh/pT6Kl/f5781e085b.png']
        gamemode_url = icons_url[gamemode]
        flag_url = 'https://new.ppy.sh//images/flags/{}.png'.format(user['country']) 

        try:
            async with aiohttp.get(bg_url) as r:
                image = await r.content.read()
            with open('data/osu/temp_bg.png','wb') as f:
                f.write(image)
            async with aiohttp.get(profile_url) as r:
                image = await r.content.read()
            with open('data/osu/temp_profile.png','wb') as f:
                f.write(image)
            async with aiohttp.get(osu_logo_url) as r:
                image = await r.content.read()
            with open('data/osu/temp_osu_logo.png','wb') as f:
                f.write(image)
            async with aiohttp.get(profile_url) as r:
                image = await r.content.read()
            with open('data/osu/temp_profile.png','wb') as f:
                f.write(image)
            async with aiohttp.get(gamemode_url) as r:
                image = await r.content.read()
            with open('data/osu/temp_gamemode.png','wb') as f:
                f.write(image)
            async with aiohttp.get(flag_url) as r:
                image = await r.content.read()
            with open('data/osu/temp_flag.png','wb') as f:
                f.write(image)
            success = True
        except Exception as e:
            success = False
            print(e)

        if success:
            with Image(filename='data/osu/temp_bg.png') as base_img:
                # background cropping as base image
                base_img.resize(600,600)
                base_img.crop(0,0,488,170)

                # draw transparent black rectangle
                with Drawing() as draw:
                    draw.fill_color = Color('#000000')
                    draw.fill_opacity = 0.6
                    draw.rectangle(left=10,top=10,right=478,bottom=160)
                    draw(base_img)

                # create level graphic
                with Drawing() as draw:
                    level_int = int(float(user['level']))
                    level_percent = float(user['level']) - level_int
                    full_length = 458
                    level_length = full_length * level_percent
                    draw.fill_color = Color('#FFF')
                    draw.fill_opacity = 0.6
                    draw.rectangle(left=15,top=145, width=level_length, bottom=155)
                    draw(base_img)
                with Drawing() as draw:
                    draw.fill_opacity = 1
                    draw.text_alignment = 'center'
                    draw.font_size = 13
                    draw.font_weight = 500
                    draw.fill_color = Color('#FFF')
                    draw.text(int(base_img.width/2), 155, "Lvl {}".format(str(level_int)))
                    draw(base_img)

                # grab user profile image
                with Image(filename='data/osu/temp_profile.png') as profile_img:
                    # user_profile image resizing
                    profile_img.resize(130,130)     
                    base_img.composite(profile_img, left=10, top=10)

                # writes lables
                with Drawing() as draw:
                    draw.text_alignment = 'right'
                    draw.font_size = 20
                    draw.font_weight = 500
                    draw.font_family = font
                    draw.fill_color = Color('#FFFFFF')
                    x = 255 # x offset
                    draw.text(x, 60, "Rank: ")
                    draw.text(x, 85, "PP: ")
                    draw.text(x, 110, "Playcount: ")
                    draw.text(x, 135, "Accuracy: ")
                    draw(base_img)

                # write user information
                with Drawing() as draw:
                    draw.font_size = 26
                    draw.font_weight = 500
                    draw.font_family = font
                    draw.text_alignment = 'center'
                    draw.fill_color = Color('#FFFFFF')
                    draw.text_decoration = 'underline'
                    draw.text(310, 35, user['username'])
                    draw(base_img)
                with Drawing() as draw:                
                    draw.font_size = 20
                    draw.font_weight = 500
                    draw.font_family = font
                    draw.fill_color = Color('#FFFFFF')
                    draw.text_decoration = 'no'
                    x = 255 # x offset
                    draw.text(x, 60, "#{} (#{})".format(user['pp_rank'], user['pp_country_rank']))
                    draw.text(x, 85, "{}".format(user['pp_raw']))
                    draw.text(x, 110, "{}".format(user['playcount']))
                    draw.text(x, 135, "{}%".format(user['accuracy'][0:5]))
                    draw(base_img)

                # draw osu with correct gamemode
                with Image(filename='data/osu/temp_osu_logo.png') as osu_icon:
                    osu_icon.resize(45,45)
                    base_img.composite(osu_icon, left=430, top=95)

                # puts on gamemode, yes, they are in order [standard, taiko, ctb, mania]
                with Image(filename='data/osu/temp_gamemode.png') as mode_icon:
                    mode_icon.resize(43,43)
                    base_img.composite(mode_icon, left=385, top=95)

                # puts on country flag
                with Image(filename='data/osu/temp_flag.png') as flag_icon:
                    flag_icon.resize(30,20) # arbitrary flag size
                    base_img.composite(flag_icon, left=440, top=17)

                # save the image
                base_img.save(filename='data/osu/user.png')

            os.remove('data/osu/temp_bg.png')
            os.remove('data/osu/temp_profile.png')
            os.remove('data/osu/temp_osu_logo.png')     
            os.remove('data/osu/temp_gamemode.png')
            os.remove('data/osu/temp_flag.png')  
        else:
            await self.bot.say("Problem generating image.")            

    # Gives a user profile image with some information
    async def draw_user_profile(self, user, userbest, gamemode:int, background:str):
        font = 'Verdana, Geneva, sans-serif'
        key = self.osu_api_key["osu_api_key"]

        # get best plays map information and scores
        best_beatmaps = []
        best_acc = []
        for i in range(len(userbest)):
            beatmap = list(await get_beatmap(key, beatmap_id=userbest[i]['beatmap_id']))[0]
            score = list(await get_scores(key, userbest[i]['beatmap_id'], user['user_id'], gamemode))[0]
            best_beatmaps.append(beatmap)
            best_acc.append(self.calculate_acc(score,gamemode))

        # get urls
        if background in bgs.keys() and background != 'random':
            bg_url = bgs[background]
        else:
            bg_url = random.choice(list(bgs.values()))  
        profile_url = 'http://s.ppy.sh/a/{}.png'.format(user['user_id'])
        osu_logo_url = 'http://puu.sh/pT7JR/577b0cc30c.png'
        icons_url=['http://puu.sh/pT2wd/4009301880.png','http://puu.sh/pT7XO/04a636cd31.png', 'http://puu.sh/pT6L5/3528ea348a.png','http://puu.sh/pT6Kl/f5781e085b.png']
        gamemode_url = icons_url[gamemode]
        flag_url = 'https://new.ppy.sh//images/flags/{}.png'.format(user['country']) 

        try:
            async with aiohttp.get(bg_url) as r:
                image = await r.content.read()
            with open('data/osu/temp_bg.png','wb') as f:
                f.write(image)
            async with aiohttp.get(profile_url) as r:
                image = await r.content.read()
            with open('data/osu/temp_profile.png','wb') as f:
                f.write(image)
            async with aiohttp.get(osu_logo_url) as r:
                image = await r.content.read()
            with open('data/osu/temp_osu_logo.png','wb') as f:
                f.write(image)
            async with aiohttp.get(profile_url) as r:
                image = await r.content.read()
            with open('data/osu/temp_profile.png','wb') as f:
                f.write(image)
            async with aiohttp.get(gamemode_url) as r:
                image = await r.content.read()
            with open('data/osu/temp_gamemode.png','wb') as f:
                f.write(image)
            async with aiohttp.get(flag_url) as r:
                image = await r.content.read()
            with open('data/osu/temp_flag.png','wb') as f:
                f.write(image)
            success = True
        except Exception as e:
            success = False
            print(e)

        if success:
            with Image(filename='data/osu/temp_bg.png') as base_img:
                # background cropping
                base_img.resize(600,600)
                base_img.crop(0,0,488,488)

                # draw transparent black rectangle
                with Drawing() as draw:
                    draw.fill_color = Color('#000000')
                    draw.fill_opacity = 0.6
                    draw.rectangle(left=10,top=10,right=478,bottom=160)
                    draw(base_img)

                # create level graphic
                with Drawing() as draw:
                    level_int = int(float(user['level']))
                    level_percent = float(user['level']) - level_int
                    full_length = 458
                    level_length = full_length * level_percent
                    draw.fill_color = Color('#FFF')
                    draw.fill_opacity = 0.6
                    draw.rectangle(left=15,top=145, width=level_length, bottom=155)
                    draw(base_img)
                with Drawing() as draw:
                    draw.fill_opacity = 1
                    draw.text_alignment = 'center'
                    draw.font_size = 13
                    draw.font_weight = 500
                    draw.fill_color = Color('#FFF')
                    draw.text(int(base_img.width/2), 155, "Lvl {}".format(str(level_int)))
                    draw(base_img)

                # draw transparent white rectangle
                with Drawing() as draw:
                    draw.fill_color = Color('#FFFFFF')
                    draw.fill_opacity = 0.6
                    draw.rectangle(left=10,top=160,right=478,bottom=478)
                    draw(base_img)

                with Image(filename='data/osu/temp_profile.png') as profile_img:
                    # user_profile image resizing
                    profile_img.resize(130,130)     
                    base_img.composite(profile_img, left=10, top=10)

                # writes lables
                with Drawing() as draw:
                    draw.text_alignment = 'right'
                    draw.font_size = 20
                    draw.font_weight = 500
                    draw.fill_color = Color('#FFFFFF')
                    x = 255 # x offset
                    draw.text(x, 60, "Rank: ")
                    draw.text(x, 85, "PP: ")
                    draw.text(x, 110, "Playcount: ")
                    draw.text(x, 135, "Accuracy: ")
                    draw(base_img)

                # write user information
                with Drawing() as draw:
                    draw.font_size = 26
                    draw.font_weight = 500
                    draw.font_family = font
                    draw.text_alignment = 'center'
                    draw.fill_color = Color('#FFFFFF')
                    draw.text_decoration = 'underline'
                    draw.text(310, 35, user['username'])
                    draw(base_img)
                with Drawing() as draw:                
                    draw.font_size = 20
                    draw.font_weight = 500
                    draw.font_family = font
                    draw.fill_color = Color('#FFFFFF')
                    draw.text_decoration = 'no'
                    x = 255 # x offset
                    draw.text(x, 60, "#{} (#{})".format(user['pp_rank'], user['pp_country_rank']))
                    draw.text(x, 85, "{}".format(user['pp_raw']))
                    draw.text(x, 110, "{}".format(user['playcount']))
                    draw.text(x, 135, "{}%".format(user['accuracy'][0:5]))
                    draw(base_img)

                # draw osu icon
                with Image(filename='data/osu/temp_osu_logo.png') as osu_icon:
                    osu_icon.resize(45,45)      
                    base_img.composite(osu_icon, left=430, top=95)

                # puts on gamemode
                with Image(filename='data/osu/temp_gamemode.png') as mode_icon:
                    mode_icon.resize(43,43)      
                    base_img.composite(mode_icon, left=385, top=95)

                # puts on country flag
                with Image(filename='data/osu/temp_flag.png') as flag_icon:
                    flag_icon.resize(30,20) # arbitrary flag size
                    base_img.composite(flag_icon, left=440, top=17)

                # writes best performances
                with Drawing() as draw:
                    draw.font_size = 28
                    draw.font_weight = 1000
                    draw.font_family = font
                    draw.text_alignment = 'center'
                    draw.fill_color = Color('#555')
                    draw.fill_opacity = 0.6
                    draw.text(244, 195, "{}".format('Best Performances'))
                    draw(base_img)            

                # create tiles for best plays using top_play_beatmaps and userbest. Includes rank, title, diff, mods, pp, timestamp
                left_align = 20
                top_initial = 210
                spacing = 53

                # draw transparent white rectangles
                for i in range(len(userbest)):
                    with Drawing() as draw:
                        draw.fill_color = Color('#CCC')
                        draw.fill_opacity = 0.6
                        draw.rectangle(left=left_align + 2,top=top_initial + spacing * i - 2, width=445, height = 45)
                        draw(base_img)

                for i in range(len(userbest)): 
                    with Drawing() as draw:
                        draw.font_size = 18
                        draw.font_weight = 500

                        # rank image
                        rank_url = 'https://new.ppy.sh/images/badges/score-ranks/{}.png'.format(userbest[i]['rank'])
                        try:
                            async with aiohttp.get(rank_url) as r:
                                image = await r.content.read()
                            with open('data/osu/temp_rank.png','wb') as f:
                                f.write(image)
                        except Exception as e:
                            print(e)

                        with Image(filename='data/osu/temp_rank.png') as rank_icon:
                            rank_icon.resize(45,45)      
                            base_img.composite(rank_icon, left=left_align + 10, top=top_initial + (i) * spacing)

                        left_text_margin = left_align + 62
                        right_text_margin = 370
                        first_line = 17
                        second_line = first_line + 20
                        draw.text(left_text_margin, top_initial + first_line + (i) * spacing, "{} ({:0.2f}%)".format(self.truncate_text(best_beatmaps[i]['title']), best_acc[i]))
                        draw.text(left_text_margin, top_initial + second_line + (i) * spacing, "[{}]".format(self.truncate_text(best_beatmaps[i]['version'])))
                        draw.text(right_text_margin, top_initial + first_line + (i) * spacing, "{:0.2f}pp".format(float(userbest[i]['pp'])))

                        # handle mod images
                        mods = self.mod_calculation(userbest[i]['enabled_mods'])
                        if len(mods) > 0:
                            for j in range(len(mods)):
                                # puts on mod images
                                mod_url = 'https://new.ppy.sh/images/badges/mods/{}.png'.format(mods[j])
                                try:
                                    async with aiohttp.get(mod_url) as r:
                                        image = await r.content.read()
                                    with open('data/osu/temp_mod.png','wb') as f:
                                        f.write(image)
                                except Exception as e:
                                    print('Issue grabbing mods.' + e)

                                with Image(filename='data/osu/temp_mod.png') as mod_icon:
                                    mod_icon.resize(30, 22)
                                    side_ways_spacing = 32
                                    base_img.composite(mod_icon, left=right_text_margin + side_ways_spacing*(j), top=top_initial + first_line + 3 + (i) * spacing) # because image
                                os.remove('data/osu/temp_mod.png')
                        draw(base_img)
                        os.remove('data/osu/temp_rank.png')
                # save the image
                base_img.save(filename='data/osu/user_profile.png')

            os.remove('data/osu/temp_bg.png')
            os.remove('data/osu/temp_profile.png')
            os.remove('data/osu/temp_osu_logo.png')     
            os.remove('data/osu/temp_gamemode.png')
            os.remove('data/osu/temp_flag.png')                  
        else:
            await self.bot.say("Problem generating image.")

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
            mod_list.append('perfect')
        if number >= 4096:
            number-= 4096
            mod_list.append('spun-out')
        if number >= 1024:
            number-= 1024
            mod_list.append('flashlight')
        if number >= 576:
            number-= 576
            mod_list.append('nightcore')
        if number >= 256:
            number-= 256
            mod_list.append('half-time')
        if number >= 128:
            number-= 128
            mod_list.append('relax')
        if number >= 64:
            number-= 64
            mod_list.append('double-time')
        if number >= 32:
            number-= 32
            mod_list.append('sudden-death')
        if number >= 16:
            number-= 16
            mod_list.append('hard-rock')
        if number >= 8:
            number-= 8
            mod_list.append('hidden')
        if number >= 2:
            number-= 2
            mod_list.append('easy')
        if number >= 1:
            number-= 1
            mod_list.append('no-fail')
        return mod_list

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
        url = re.search("(?P<url>https?://[^\s]+)", message.content).group("url")
        if url.find('https://osu.ppy.sh/s/') != -1:
            beatmap_id = url.replace('https://osu.ppy.sh/s/','')
            beatmap_info = await get_beatmapset(key, beatmap_id)
        elif url.find('https://osu.ppy.sh/b/') != -1:
            beatmap_id = url.replace('https://osu.ppy.sh/b/','')
            beatmap_info = await get_beatmap(key, beatmap_id)
        await self.disp_beatmap(message, beatmap_info)
        '''
        except:
            await self.bot.send_message(message.channel, "That beatmap doesn't exist.")
        '''     

    # displays the beatmap properly
    async def disp_beatmap(self, message, beatmap):
        # process time

        max_disp = 3
        num_disp = min(len(beatmap), max_disp)
        if (len(beatmap)>max_disp):
            await self.bot.send_message(message.channel, "Found {} maps, but only displaying {}.\n".format(len(beatmap), max_disp))            
        else:
            await self.bot.send_message(message.channel, "Found {} map(s).\n".format(len(beatmap)))

        beatmap_msg = ""               
        for i in range(num_disp):
            if i == 0:
                beatmap_msg = "```xl\n{} - {}```\n".format(beatmap[i]['title'],beatmap[i]['artist'])
            beatmap_msg += "```xln\n"
            beatmap_msg += "Version: [{}] by {}\n".format(beatmap[i]['version'], beatmap[i]['creator'])
            m, s = divmod(int(beatmap[i]['total_length']), 60)
            beatmap_msg += "Difficulty: {:.2f}★ BPM: {} Length: {}m {}s \n".format(float(beatmap[i]['difficultyrating']), beatmap[i]['bpm'], m, s)
            beatmap_msg += "AR: {} OD: {} HP: {} CS: {}\n".format(beatmap[i]['diff_approach'], beatmap[i]['diff_overall'], beatmap[i]['diff_drain'], beatmap[i]['diff_size'])
            beatmap_msg += "```"
        await self.bot.send_message(message.channel, beatmap_msg)


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

def setup(bot):
    check_folders()
    check_files()

    try: 
        from wand.image import Image, COMPOSITE_OPERATORS
        from wand.drawing import Drawing
        from wand.display import display
        from wand.image import Image
        from wand.color import Color
    except:
        raise ModuleNotFound("Wand is not installed. Do 'pip3 install Wand --upgrade' and make sure you have ImageMagick installed http://docs.wand-py.org/en/0.4.2/guide/install.html")
    n = Osu(bot)
    bot.add_listener(n.find_beatmap, "on_message")    
    bot.add_cog(n)