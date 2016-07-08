import discord
import json, re, sys, urllib.request, urllib.parse, urllib.error
import codecs
import requests
import random
import os
from discord.ext import commands
from urllib.request import urlopen
from .utils.dataIO import fileIO
from wand.image import Image
from wand.display import display
from wand.drawing import Drawing
from wand.color import Color
from cogs.utils import checks

bg_urls = ['http://puu.sh/pUeKt/bd02db94a1.jpg', 'http://puu.sh/pUdMe/4cdc33ed08.jpg','http://puu.sh/pUdJb/47220936c9.jpg','http://puu.sh/pUdBf/8959a98929.png','http://puu.sh/pUdyQ/62eee8b326.jpg','http://puu.sh/pSSFN/34704f54e7.jpg', 'http://puu.sh/pSSHJ/20fd045df0.jpg','http://puu.sh/pSSKb/0bbe644cce.png', 'http://puu.sh/pST3z/238863993a.png','http://puu.sh/pST4a/563337774d.jpg']
help_msg = "You either don't exist in the database, haven't played enough, or don't have an osu api key (*it's required*). You can get one from https://osu.ppy.sh/p/api. If already have a key, do **<p>osukeyset** to set your key"

class Osu:
    """Cog to give osu! stats for all gamemodes, hopefully."""

    def __init__(self, bot):
        self.bot = bot
        self.osu_api_key = fileIO("data/osu/apikey.json", "load")

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def osukeyset(self, ctx):
        """Sets your osu api key"""

        await self.bot.whisper("Type your osu api key. You can reply here.")
        key = await self.bot.wait_for_message(timeout=30,
                                                   author=ctx.message.author)
        if key is None:
            return
        else:
            self.osu_api_key["osu_api_key"] = key.content
            fileIO("data/osu/apikey.json", "save", self.osu_api_key)
            await self.bot.whisper("API Key details added.")

    @commands.command(pass_context=True, no_pm=True)
    async def osu(self, ctx, *, username):
        """Gives osu! standard user stats"""
        key = self.osu_api_key["osu_api_key"]
        msg = ctx.message
        author = ctx.message.author
        channel = ctx.message.channel

        try:
          userinfo = get_user(key, username, 0, "Autodetect", 1).decode("utf-8")
          if (len(json.loads(userinfo)) > 0):
            self.user_small(json.loads(userinfo)[0], 0)
            await self.bot.send_typing(channel)
            await self.bot.send_file(channel, 'user.png')
          else:
            await self.bot.say("Player not found :cry:")
        except:
          await self.bot.say(help_msg)

    @commands.command(pass_context=True, no_pm=True)
    async def taiko(self, ctx, *, username):
        """Gives taiko user stats"""
        key = self.osu_api_key["osu_api_key"]
        msg = ctx.message
        author = ctx.message.author
        channel = ctx.message.channel

        try:
            userinfo = get_user(key, username, 1, "Autodetect", 1).decode("utf-8")
            if (len(json.loads(userinfo)) > 0):
              self.user_small(json.loads(userinfo)[0], 1)
              await self.bot.send_typing(channel)
              await self.bot.send_file(channel, 'user.png')
            else:
              await self.bot.say("Player not found :cry:")
        except:
          await self.bot.say(help_msg)

    @commands.command(pass_context=True, no_pm=True)
    async def ctb(self, ctx, *, username):
        """Gives Catch the Beat user stats"""
        key = self.osu_api_key["osu_api_key"]
        msg = ctx.message
        author = ctx.message.author
        channel = ctx.message.channel

        try:
            userinfo = get_user(key, username, 2, "Autodetect", 1).decode("utf-8")
            if (len(json.loads(userinfo)) > 0):
              self.user_small(json.loads(userinfo)[0], 2)
              await self.bot.send_typing(channel)
              await self.bot.send_file(channel, 'user.png')
            else:
              await self.bot.say("Player not found :cry:")
        except:
          await self.bot.say(help_msg)

    @commands.command(pass_context=True, no_pm=True)
    async def mania(self, ctx, *, username):
        """Gives osu standard user stats"""

        key = self.osu_api_key["osu_api_key"]
        msg = ctx.message
        author = ctx.message.author
        channel = ctx.message.channel

        try: 
            userinfo = get_user(key, username, 3, "Autodetect", 1).decode("utf-8")
            if (len(json.loads(userinfo)) > 0):
              self.user_small(json.loads(userinfo)[0], 3)
              await self.bot.send_typing(channel)
              await self.bot.send_file(channel, 'user.png')
            else:
              await self.bot.say("Player not found :cry:")
        except:
          await self.bot.say(help_msg)

    @commands.command(pass_context=True, no_pm=True)
    async def osuprofile(self, ctx, *, username):
        """Gives osu! standard user best plays"""
        key = self.osu_api_key["osu_api_key"]
        msg = ctx.message
        author = ctx.message.author
        channel = ctx.message.channel
         
        # get userinfo
        userinfo = get_user(key, username, 0, "Autodetect", 1).decode("utf-8")
        userbest = get_user_best(key, username, 0, 3, "Autodetect").decode("utf-8")

        if (len(json.loads(userinfo)) > 0):
          self.user_profile(json.loads(userinfo)[0],json.loads(userbest), 0) # only takes the first one
          await self.bot.send_typing(channel)
          await self.bot.send_file(channel, 'user.png')
        else:
          await self.bot.say("Player not found :cry:")


    @commands.command(pass_context=True, no_pm=True)
    async def taikoprofile(self, ctx, *, username):
        """Gives taiko user stats and best plays"""
        key = self.osu_api_key["osu_api_key"]
        msg = ctx.message
        author = ctx.message.author
        channel = ctx.message.channel
        try: 
            # get userinfo
            userinfo = get_user(key, username, 1, "Autodetect", 1).decode("utf-8")
            userbest = get_user_best(key, username, 1, 3, "Autodetect").decode("utf-8")

            if (len(json.loads(userinfo)) > 0):
              self.user_profile(json.loads(userinfo)[0],json.loads(userbest), 1) # only takes the first one
              await self.bot.send_typing(channel)
              await self.bot.send_file(channel, 'user.png')
            else:
              await self.bot.say("Player not found :cry:")
        except:
            await self.bot.say(help_msg)

    @commands.command(pass_context=True, no_pm=True)
    async def ctbprofile(self, ctx, *, username):
        """Gives ctb user stats and best plays"""
        key = self.osu_api_key["osu_api_key"]
        msg = ctx.message
        author = ctx.message.author
        channel = ctx.message.channel
        try: 
            # get userinfo
            userinfo = get_user(key, username, 2, "Autodetect", 1).decode("utf-8")
            userbest = get_user_best(key, username, 2, 3, "Autodetect").decode("utf-8")

            if (len(json.loads(userinfo)) > 0):
              self.user_profile(json.loads(userinfo)[0],json.loads(userbest), 2) # only takes the first one
              await self.bot.send_typing(channel)
              await self.bot.send_file(channel, 'user.png')
            else:
              await self.bot.say("Player not found :cry:")
        except:
            await self.bot.say(help_msg)

    @commands.command(pass_context=True, no_pm=True)
    async def maniaprofile(self, ctx, *, username):
        """Gives osu! mania user stats and best plays"""
        key = self.osu_api_key["osu_api_key"]
        msg = ctx.message
        author = ctx.message.author
        channel = ctx.message.channel
        try: 
            # get userinfo
            userinfo = get_user(key, username, 3, "Autodetect", 1).decode("utf-8")
            userbest = get_user_best(key, username, 3, 3, "Autodetect").decode("utf-8")

            if (len(json.loads(userinfo)) > 0):
              self.user_profile(json.loads(userinfo)[0],json.loads(userbest), 3) # only takes the first one
              await self.bot.send_typing(channel)
              await self.bot.send_file(channel, 'user.png')
            else:
              await self.bot.say("Player not found :cry:")
        except:
            await self.bot.say(help_msg)

    def user_small(self, user, gamemode):
        """Gives a small user profile image"""

        # get user
        gamemode = int(gamemode)
        user = user
        font = 'Verdana, Geneva, sans-serif'

        # generate background and crops image to correct size
        bg_url = bg_urls[random.randint(0,len(bg_urls))-1]
        bg_req = urllib.request.Request(bg_url, headers={'User-Agent': 'Mozilla/5.0'})
        bg = urlopen(bg_req)
        with Image(file=bg) as base_img:
            # background cropping
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
            profile_url = 'http://s.ppy.sh/a/{}.png'.format(user['user_id'])
            profile_req = urllib.request.Request(profile_url, headers={'User-Agent': 'Mozilla/5.0'})
            profile = urlopen(profile_req)
            with Image(file=profile) as profile_img:
                # user_profile image resizing
                profile_img.resize(130,130)    	
                base_img.composite(profile_img, left=10, top=10)
            profile.close()

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
            osu_logo_url = 'http://puu.sh/pT7JR/577b0cc30c.png'
            osu_req = urllib.request.Request(osu_logo_url, headers={'User-Agent': 'Mozilla/5.0'})
            osu = urlopen(osu_req)
            with Image(file=osu) as osu_icon:
                osu_icon.resize(45,45)
                base_img.composite(osu_icon, left=430, top=95)
            osu.close()

            # puts on gamemode
            # yes, they are in order [standard, taiko, ctb, mania]
            icons_url=['http://puu.sh/pT2wd/4009301880.png','http://puu.sh/pT7XO/04a636cd31.png', 'http://puu.sh/pT6L5/3528ea348a.png','http://puu.sh/pT6Kl/f5781e085b.png']
            mode_url = icons_url[gamemode]
            mode_req = urllib.request.Request(mode_url, headers={'User-Agent': 'Mozilla/5.0'})
            mode = urlopen(mode_req)
            with Image(file=mode) as mode_icon:
                mode_icon.resize(43,43)
                base_img.composite(mode_icon, left=385, top=95)
            mode.close()

            # puts on country flag
            flag_url = 'https://new.ppy.sh//images/flags/{}.png'.format(user['country'])
            flag_req = urllib.request.Request(flag_url, headers={'User-Agent': 'Mozilla/5.0'})
            flag = urlopen(flag_req)
            with Image(file=flag) as flag_icon:
                flag_icon.resize(30,20) # arbitrary flag size
                base_img.composite(flag_icon, left=440, top=17)
            flag.close()

            # save the image
            base_img.save(filename='user.png')
        bg.close()

    # user and userbest comes in json format
    def user_profile(self, user, userbest, gamemode):
        """Gives a user profile image with some information"""
        font = 'Verdana, Geneva, sans-serif'
        key = self.osu_api_key["osu_api_key"]

        ## handle data retrieval for top beatmaps
        gamemode = int(gamemode)

        # get best plays map titles
        best_beatmaps = []
        for i in range(len(userbest)):
            beatmap = json.loads(get_beatmap(key, beatmap_id=userbest[i]['beatmap_id']).decode("utf-8"))
            best_beatmaps.append(beatmap[0])

        # generate background and crops image to correct size
        bg_url = bg_urls[random.randint(0,len(bg_urls))-1]
        bg_req = urllib.request.Request(bg_url, headers={'User-Agent': 'Mozilla/5.0'})
        bg = urlopen(bg_req)
        with Image(file=bg) as base_img:
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

            # grab user profile image
            profile_url = 'http://s.ppy.sh/a/{}.png'.format(user['user_id'])
            profile_req = urllib.request.Request(profile_url, headers={'User-Agent': 'Mozilla/5.0'})
            profile = urlopen(profile_req)
            with Image(file=profile) as profile_img:
                # user_profile image resizing
                profile_img.resize(130,130)     
                base_img.composite(profile_img, left=10, top=10)
            profile.close()

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
            osu_logo_url = 'http://puu.sh/pT7JR/577b0cc30c.png'
            osu_req = urllib.request.Request(osu_logo_url, headers={'User-Agent': 'Mozilla/5.0'})
            osu = urlopen(osu_req)
            with Image(file=osu) as osu_icon:
                osu_icon.resize(45,45)      
                base_img.composite(osu_icon, left=430, top=95)
            osu.close()

            # puts on gamemode
            # yes, they are in order [standard, taiko, ctb, mania]
            icons_url=['http://puu.sh/pT2wd/4009301880.png','http://puu.sh/pT7XO/04a636cd31.png', 'http://puu.sh/pT6L5/3528ea348a.png','http://puu.sh/pT6Kl/f5781e085b.png']
            mode_url = icons_url[gamemode]
            mode_req = urllib.request.Request(mode_url, headers={'User-Agent': 'Mozilla/5.0'})
            mode = urlopen(mode_req)
            with Image(file=mode) as mode_icon:
                mode_icon.resize(43,43)      
                base_img.composite(mode_icon, left=385, top=95)
            mode.close()

            # puts on country flag
            flag_url = 'https://new.ppy.sh//images/flags/{}.png'.format(user['country'])
            flag_req = urllib.request.Request(flag_url, headers={'User-Agent': 'Mozilla/5.0'})
            flag = urlopen(flag_req)
            with Image(file=flag) as flag_icon:
                flag_icon.resize(30,20) # arbitrary flag size
                base_img.composite(flag_icon, left=440, top=17)
            flag.close()

            # writes best performances
            with Drawing() as draw:
                draw.font_size = 32
                draw.font_weight = 1000
                draw.font_family = font
                draw.text_alignment = 'center'
                draw.fill_color = Color('#555')
                draw.fill_opacity = 0.6
                draw.text(244, 205, "{}".format('Best Performances'))
                draw(base_img)            

            # create tiles for best plays using top_play_beatmaps and userbest. Includes rank, title, diff, mods, pp, timestamp
            left_align = 20
            top_initial = 230
            spacing = 85

            # draw transparent white rectangles
            for i in range(3):
              with Drawing() as draw:
                  draw.fill_color = Color('#CCC')
                  draw.fill_opacity = 0.6
                  draw.rectangle(left=left_align + 2,top=top_initial + spacing * i - 5, width=445, height = 70)
                  draw(base_img)

            for i in range(len(userbest)): 
              with Drawing() as draw:
                  draw.font_size = 24
                  draw.font_weight = 2000

                  # rank image
                  rank_url = 'https://new.ppy.sh/images/badges/score-ranks/{}.png'.format(userbest[i]['rank'])
                  rank_req = urllib.request.Request(rank_url, headers={'User-Agent': 'Mozilla/5.0'})
                  rank = urlopen(rank_req)
                  with Image(file=rank) as rank_icon:
                    rank_icon.resize(70,70)      
                    base_img.composite(rank_icon, left=left_align, top=top_initial + (i) * spacing)
                  rank.close() 

                  draw.text(left_align + 100, top_initial + 30 + (i) * spacing, "{}".format(truncate_text(best_beatmaps[i]['title'])))
                  draw.text(left_align + 100, top_initial + 50 + (i) * spacing, "[{}]".format(truncate_text(best_beatmaps[i]['version'])))

                  draw.text(left_align + 320, top_initial + 30 + (i) * spacing, "{}pp".format(userbest[i]['pp']))

                  # handle mod images
                  mods = mod_calculation(userbest[i]['enabled_mods'])
                  if len(mods) > 0:
                    for j in range(len(mods)):
                      # puts on mod images
                      mod_url = 'https://new.ppy.sh/images/badges/mods/{}.png'.format(mods[j])
                      mod_req = urllib.request.Request(mod_url, headers={'User-Agent': 'Mozilla/5.0'})
                      mod = urlopen(mod_req)
                      with Image(file=mod) as mod_icon:
                          mod_icon.resize(46, 34)
                          base_img.composite(mod_icon, left=left_align + 315 + 45*(j), top=top_initial + 32 + (i) * spacing)
                      mod.close()
                  draw(base_img)

            # save the image
            base_img.save(filename='user.png')
        bg.close()

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# other helpers
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def truncate_text(text):
  if len(text) > 17:
    text = text[0:17] + '...'
  return text

# gives a list of the ranked mods
def mod_calculation(number):
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

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# osu!apy Methods written by albinohat (https://github.com/albinohat/osu-apy)
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## build_request - Returns the full API request URL using the provided base URL and parameters.
## list_params   - The list of parameters to add to the end of the request URL.
## URL - The base API request URL to append the list of parameters to.
def build_request(list_of_params, url):
  ''' Build the request URL.'''
  for param in list_of_params:
    url += str(param)
    if (param != ""):
      url += "&"
  
  ## Remove the trailing '&' because I'm OCD.
  return url[:-1]

## get_beatmaps - Returns a JSON payload containing information about a beatmap set or beatmap.
## key          - Your API key. (Required)
## since        - A MYSQL-formatted date which is the cut off for the returned data.
## set_id       - A beatmap set ID. 
## beatmap_id   - A beatmap ID. 
## user_id      - A user ID. 
def get_beatmap(key, beatmap_id):
  ''' Create a list to store the attributes which are present.'''
  list_of_params = []

  ## Populate the list of PHP variables.
  ## Only prepend the PHP variable names if they are there.
  list_of_params.append(parameterize_key(key))
  list_of_params.append(parameterize_id("b", beatmap_id)) 

  ## Build the request URLand return the response.
  return urllib.request.urlopen(build_request(list_of_params, "https://osu.ppy.sh/api/get_beatmaps?")).read()

## get_match - Returns information about multiplayer match.
## key       - Your API key. (Required)
## multi_id  - A multiplayer match ID.
def get_match(key, multi_id):
  '''Create a list to store the attributes which are present.'''
  list_of_params = []

  ## Populate the list of PHP variables.
  ## Only prepend the PHP variable names if they are there.
  list_of_params.append(parameterize_key(key))
  list_of_params.append(parameterize_id("mp", multi_id))  

  ## Build the request URLand return the response.
  return urllib.request.urlopen(build_request(list_of_params, "https://osu.ppy.sh/api/get_beatmaps?")).read()

## get_scores - Returns information about the top 50 scores of a specified beatmap.
## key        - Your API key.
## beatmap_id - A beatmap ID. 
## user_id    - A user ID.
## mode       - The game mode for which to get info. 
##                  (0 = osu!, 1 = Taiko, 2 = CtB, 3 = osu!mania, Default = 0)
def get_scores(key, beatmap_id, user_id, mode):
  ''' Create a list to store the attributes which are present.'''
  list_of_params = []

  ## Populate the list of PHP variables.
  ## Only prepend the PHP variable names if they are there.
  list_of_params.append(parameterize_key(key))
  list_of_params.append(parameterize_id("b", beatmap_id))   
  list_of_params.append(parameterize_id("u", user_id))
  list_of_params.append(parameterize_mode(mode))

  ## Build the full request URL and return the response.
  return urllib.request.urlopen(build_request(list_of_params, "https://osu.ppy.sh/api/get_scores?")).read()

## get_user - Returns a JSON payload containing information about a beatmap set or beatmap.
## key        - Your API key. (Required)
## user_id    - A user ID. (Required)
## mode       - The game mode for which to get info. 
##                  (0 = osu!, 1 = Taiko, 2 = CtB, 3 = osu!mania, Default = 0)
## type       - Specifies rather the user_id specified is an ID or a username. 
##                  (id = id, string = username, default = Autodetect)
## event_days - Maximum number of days between now and last event date. 
##                  (1 - 31, default = 1)
def get_user(key, user_id, mode, type, event_days): 
  ''' Create a list to store the attributes which are present.'''
  list_of_params = []

  ## Populate the list of PHP variables.  
  ## Only prepend the PHP variable names if they are there.
  list_of_params.append(parameterize_key(key))
  list_of_params.append(parameterize_id("u", user_id))
  list_of_params.append(parameterize_mode(mode))
  list_of_params.append(parameterize_type(type))
  list_of_params.append(parameterize_event_days(event_days))

  ## Build the request URL and return the response.
  return urllib.request.urlopen(build_request(list_of_params, "https://osu.ppy.sh/api/get_user?")).read()

## get_user_best - Returns the top scores for the specified user.
## key           - Your API key. (Required)
## user_id       - A user ID. (Required)
## mode          - The game mode for which to get info. 
##                     (0 = osu!, 1 = Taiko, 2 = CtB, 3 = osu!mania, Default = 0)
## limit         - # of results to return. 
##                     (1 - 50, Default = 10).
## type          - Specifies rather the user_id specified is an ID or a username. 
##                     (id = id, string = username, default = Autodetect)
def get_user_best(key, user_id, mode, limit, type):
  ''' Create a list to store the attributes which are present.'''
  list_of_params = []

  ## Populate the list of PHP variables.
  ## Only prepend the PHP variable names if they are there.
  list_of_params.append(parameterize_key(key))
  list_of_params.append(parameterize_id("u", user_id))
  list_of_params.append(parameterize_mode(mode))
  list_of_params.append(parameterize_limit(limit))
  list_of_params.append(parameterize_type(type))  

  ## Build the full request URL and return the response.
  return urllib.request.urlopen(build_request(list_of_params, "https://osu.ppy.sh/api/get_user_best?")).read()

## get_user_recent - Returns the user's ten most recent plays.
## key             - Your API key. (Required)
## user_id         - A user ID. (Required)
## mode            - The game mode for which to get info.
##                       (0 = osu!, 1 = Taiko, 2 = CtB, 3 = osu!mania, Default = 0)
## type            - Specifies rather the user_id specified is an ID or a username. 
##                       (id = id, string = username, default = Autodetect)
def get_user_recent(key, user_id, mode, type):
  ''' Create a list to store the attributes which are present.'''
  list_of_params = []

  ## Populate the list of PHP variables.
  ## Only prepend the PHP variable names if they are there.
  list_of_params.append(parameterize_key(key))
  list_of_params.append(parameterize_id("u", user_id))
  list_of_params.append(parameterize_mode(mode))
  list_of_params.append(parameterize_type(type))  

  ## Build the full request URL and return the response.
  return urllib.request.urlopen(build_request(list_of_params, "https://osu.ppy.sh/api/get_user_recent?")).read()

def parameterize_event_days(event_days):
  ''' parameterize_event_days - Formats event days as a PHP parameter.'''
  if (event_days == ""):
    event_days = "event_days=1"
  elif (int(event_days) >= 1 and int(event_days) <= 31):
    event_days = "event_days=" + str(event_days)
  else:
    print("    Invalid event_days \"" + str(event_days) + ".\"")

  return event_days

## parameterize_id - Formats an ID as a PHP parameter.
## t               - The type of ID.
##                       (b = beatmap, s = beatmap set, u = user)
## id              - A beatmap, beatmap set, or user ID.
def parameterize_id(t, id):
  if (t != "b" and t != "s" and t != "u" and t != "mp"):
    print("    Invalid type \"" + str(t) + ".\"")
    sys.exit()
  
  if (len(str(id)) != 0):
    return t + "=" + str(id)
  else:
    return ""

## parameterize_key - Formats an API key as a PHP parameter.
## key              - An API key.
def parameterize_key(key):
  if (len(key) == 40):
    return "k=" + key
  else:
    print("    Invalid key \"" + str(key) + ".\"")   

## parameterize_limit - Formats the limit as a PHP parameter.
## limit              - The maximum # of scores to show.
def parameterize_limit(limit):
  ## Default case: 10 scores
  if (limit == ""):
    limit = "limit=10"
  elif (int(limit) >= 1 and int(limit) <= 50):
    limit = "limit=" + str(limit)
  else:
    print("    Invalid limit \"" + str(limit) + ".\"")
  
  return limit
  
## parameterize_mode - Formats a mode as a PHP parameter.
## mode              - The game mode for which to get info.
def parameterize_mode(mode):
  ## Default case: 0 (osu!)
  if (mode == ""):
    mode = "m=0"
  elif (int(mode) >= 0 and int(mode) <= 3):
    mode = "m=" + str(mode)
  else:
    print("    Invalid mode \"" + str(mode) + ".\"")
  
  return mode

## parameterize_since - Formats a since as a PHP parameter.
## since              - A MYSQL-formatted date which is the cut off for the time period in which to return data.
def parameterize_since(since):
  if (since == ""):
    return since
  if (re.match("[0-9]{4}\-[0-1]?[1-9]\-[0-3]?[1-9] [0-2]?[0-9]\:[0-5][0-9]\:[0-5][0-9]", since)):
    return "since=" + str(since)
  else:
    print("    Invalid since \"" + str(since) + ".\"")  
  
## parameterize_type - Formats a type as a PHP parameter.
## type              - Specifies rather the user_id specified is an ID or a username.
def parameterize_type(type):
  if (type == ""):
    return type
  elif (type == "id" or type == "string"):
    return  "type=" + str(type)
  else:
    print("    Invalid type \"" + str(type) + ".\"")  

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Set-up
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------    
def check_folders():
    if not os.path.exists("data/osu"):
        print("Creating data/osu folder...")
        os.makedirs("data/osu")

def check_files():
    osu_api_key = {"osu_api_key" : ""}
    credential_file = "data/osu/apikey.json"

    if not fileIO(credential_file, "check"):
        print("Adding data/osu/apikey.json...")
        fileIO(credential_file, "save", osu_api_key)
    else:  # consistency check
        current = fileIO(credential_file, "load")
        if current.keys() != osu_api_key.keys():
            for key in system.keys():
                if key not in osu_api_key.keys():
                    current[key] = osu_api_key[key]
                    print("Adding " + str(key) +
                          " field to osu apikey.json")
            fileIO(credential_file, "save", current)

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
  bot.add_cog(Osu(bot))