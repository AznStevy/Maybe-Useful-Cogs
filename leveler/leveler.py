import discord
from discord.ext import commands
import random
import os
from .utils.dataIO import fileIO
from cogs.utils import checks
import textwrap
import aiohttp
import operator
try:
    from PIL import Image, ImageDraw, ImageFont, ImageColor
    pil_available = True
except:
    pil_available = False
import time

prefix = fileIO("data/red/settings.json", "load")['PREFIXES'][0]

# fonts
name_fnt = ImageFont.truetype('data/leveler/fonts/font_bold.ttf', 18)
title_fnt = ImageFont.truetype('data/leveler/fonts/font.ttf', 18)
sub_header_fnt = ImageFont.truetype('data/leveler/fonts/font_bold.ttf', 14)
exp_fnt = ImageFont.truetype('data/leveler/fonts/font.ttf', 14)
level_fnt = ImageFont.truetype('data/leveler/fonts/font_bold.ttf', 30)
level_label_fnt = ImageFont.truetype('data/leveler/fonts/font_bold.ttf', 20)
rep_fnt = ImageFont.truetype('data/leveler/fonts/font_bold.ttf', 32)
text_fnt = ImageFont.truetype('data/leveler/fonts/font_bold.ttf', 12)

class Leveler:
    """A level up thing with image generation!"""

    def __init__(self, bot):
        self.bot = bot
        self.users = fileIO("data/leveler/users.json", "load")
        self.block = fileIO("data/leveler/block.json", "load")

    @commands.command(pass_context=True, no_pm=True)
    async def profile(self,ctx, *, user : discord.Member=None):
        """Displays a user profile."""
        if user == None:
            user = ctx.message.author
        channel = ctx.message.channel
        server = user.server

        await self.draw_profile(user, server)
        await self.bot.send_typing(channel)         
        await self.bot.send_file(channel, 'data/leveler/profile.png', content='**User profile for {}**'.format(user.mention)) 

    @commands.command(pass_context=True, no_pm=True)
    async def rank(self,ctx,user : discord.Member=None):
        """Displays the rank of a user."""
        if user == None:
            user = ctx.message.author
        channel = ctx.message.channel
        server = user.server

        # get urls
        await self.draw_rank(user, server)
        await self.bot.send_typing(channel)            
        await self.bot.send_file(channel, 'data/leveler/rank.png', content='**Ranking & Statistics for {}**'.format(user.mention))

    @commands.command(pass_context=True, no_pm=True)
    async def top10(self,ctx):
        server = ctx.message.server
        userinfo = self.users[server.id]

        msg = "**Leaderboard for {}**\n".format(server.name)
        users = []
        for userkey in userinfo.keys():
            users.append((userkey, userinfo[userkey]["name"], userinfo[userkey]["total_exp"]))
        sorted_list = sorted(users, key=operator.itemgetter(2), reverse=True)

        msg += "```ruby\n"
        rank = 1
        labels = ["♚","⛊","✪", " ", " ", " ", " ", " ", " ", " "]
        for user in sorted_list[:10]:
            msg += u'{:<2}{:<2}{:<2}   # {:<5}\n'.format(rank, labels[rank-1], "➤", user[1])
            msg += u'{:<2}{:<2}{:<2}    {:<5}\n'.format(" ", " ", " ", "Total Points: " + str(user[2]))
            rank += 1
        msg +="```"
        await self.bot.say(msg)        

    @commands.command(pass_context=True, no_pm=True)
    async def rep(self, ctx, user : discord.Member):
        """Gives a reputation point to a designated player."""
        org_user = ctx.message.author
        channel = ctx.message.channel
        server = user.server
        curr_time = time.time()

        if user.id == org_user.id:
            await self.bot.say("**You can't give a rep to yourself!**")
            return
        if user.bot:
            await self.bot.say("**You can't give a rep to a bot!**")
            return

        if server.id not in self.block:
            self.block[server.id] = {}
            fileIO('data/leveler/block.json', "save", self.block)
        if org_user.id not in self.block[server.id]:
            self.block[server.id][org_user.id] = {
                "chat": time.time(),
                "rep" : time.time()
            }
            fileIO('data/leveler/block.json', "save", self.block)

        if float(curr_time) - float(self.block[server.id][user.id]["rep"]) >= 43200.0:
            self.block[server.id][org_user.id]["rep"] = time.time()
            self.users[server.id][user.id]["rep"] += 1
            fileIO('data/leveler/block.json', "save", self.block)
            fileIO('data/leveler/users.json', "save", self.users)
            await self.bot.say("**You have just given {} a reputation point!**".format(user.mention))
        else:
            # calulate time left
            seconds = 43200 - (curr_time - self.block[server.id][org_user.id]["rep"])
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            await self.bot.say("**You need to wait {} hours, {} minutes, and {} seconds until you can give reputation again!**".format(int(h), int(m), int(s)))

    @commands.command(pass_context=True, no_pm=True)
    async def title(self, ctx, *, title):
        """Set your title."""
        user = ctx.message.author
        server = ctx.message.server
        max_char = 20

        if len(title) < max_char:
            self.users[server.id][user.id]["title"] = title
            fileIO('data/leveler/users.json', "save", self.users)
            await self.bot.say("**Your title has been succesfully set!**")
        else:
            await self.bot.say("**Your title has too many characters! Must be <{}**".format(max_char))

    @commands.command(pass_context=True, no_pm=True)
    async def setinfo(self, ctx, *, info):
        """Set your user info."""
        user = ctx.message.author
        server = ctx.message.server
        max_char = 150

        if len(info) < max_char:
            self.users[server.id][user.id]["info"] = info
            fileIO('data/leveler/users.json', "save", self.users)
            await self.bot.say("**Your info section has been succesfully set!**")
        else:
            await self.bot.say("**Your description has too many characters! Must be <{}**".format(max_char))

    @commands.command(pass_context=True, no_pm=True)
    async def setprofilebg(self, ctx, *, url):
        """Grab the url from tatsumaki page"""
        user = ctx.message.author
        server = ctx.message.server

        if "http://tatsumaki.xyz/images/backgrounds/profile/" in url:
            self.users[server.id][user.id]["profile_background"] = url
            fileIO('data/leveler/users.json', "save", self.users)
            await self.bot.say("**Your new profile background has been succesfully set!**")
        else:
            await self.bot.say("That's not a valid url. It should follow: http://tatsumaki.xyz/images/backgrounds/profile/")

    @commands.command(pass_context=True, no_pm=True)
    async def setrankbg(self, ctx, *, url):
        """Grab the url from tatsumaki page"""
        user = ctx.message.author
        server = ctx.message.server

        if "http://tatsumaki.xyz/images/backgrounds/rank/" in url:
            self.users[server.id][user.id]["rank_background"] = url
            fileIO('data/leveler/users.json', "save", self.users)
            await self.bot.say("**Your new rank background has been succesfully set!**")
        else:
            await self.bot.say("That's not a valid url. It should follow: http://tatsumaki.xyz/images/backgrounds/rank/")

    @commands.command(pass_context=True, no_pm=True)
    async def setlevelbg(self, ctx, *, url):
        """Grab the url from tatsumaki page"""
        user = ctx.message.author
        server = ctx.message.server

        if "http://tatsumaki.xyz/images/backgrounds/levelup/" in url:
            self.users[server.id][user.id]["levelup_background"] = url
            fileIO('data/leveler/users.json', "save", self.users)
            await self.bot.say("**Your new level-up background has been succesfully set!**")
        else:
            await self.bot.say("That's not a valid url. It should follow: http://tatsumaki.xyz/images/backgrounds/levelup/")

    async def draw_profile(self, user, server):
        # get urls
        userinfo = self.users[server.id][user.id]
        bg_url = userinfo["profile_background"]
        profile_url = user.avatar_url         
        discord_url = 'http://puu.sh/qxCqL/2d35aea5d6.png'
        info_icon_url = 'http://puu.sh/qxCsi/d649552d29.png'

        # create image objects
        bg_image = Image
        profile_image = Image
        discord_image = Image
        info_image = Image       
    
        async with aiohttp.get(bg_url) as r:
            image = await r.content.read()
        with open('data/leveler/temp_bg.png','wb') as f:
            f.write(image)
        async with aiohttp.get(profile_url) as r:
            image = await r.content.read()
        with open('data/leveler/temp_profile.png','wb') as f:
            f.write(image)
        async with aiohttp.get(discord_url) as r:
            image = await r.content.read()
        with open('data/leveler/temp_discord_logo.png','wb') as f:
            f.write(image)
        async with aiohttp.get(info_icon_url) as r:
            image = await r.content.read()
        with open('data/leveler/temp_info.png','wb') as f:
            f.write(image)

        bg_image = Image.open('data/leveler/temp_bg.png').convert('RGBA')            
        profile_image = Image.open('data/leveler/temp_profile.png').convert('RGBA')
        discord_image = Image.open('data/leveler/temp_discord_logo.png').convert('RGBA')
        info_image = Image.open('data/leveler/temp_info.png').convert('RGBA') 

        # set canvas
        bg_color = (255,255,255,0)
        result = Image.new('RGBA', (290, 290), bg_color)
        process = Image.new('RGBA', (290, 290), bg_color)

        # draw
        draw = ImageDraw.Draw(process)

        # puts in background
        bg_image = bg_image.resize((290, 290), Image.ANTIALIAS)
        bg_image = bg_image.crop((0,0, 290, 290))
        result.paste(bg_image, (0,0))

        # draw filter
        draw.rectangle([(0,0),(290, 290)], fill=(0,0,0,10))

        # draw transparent overlay           
        draw.rectangle([(5,100), (285, 135)], fill=(50,50,50,200)) # header
        draw.rectangle([(100,135), (285, 285)], fill=(200,200,200,230)) # main content
        draw.rectangle([(5,135), (100, 170)], fill=(92,130,203,230)) # reps
        draw.rectangle([(5,170), (100, 285)], fill=(128,151,165,230)) # badges
        draw.rectangle([(12,60), (92,140)], fill=(255,255,255, 160), outline=(255, 255, 255, 160)) # profile square

        # put in profile picture
        profile_size = (77, 77)
        profile_image = profile_image.resize(profile_size, Image.ANTIALIAS)
        process.paste(profile_image, (14, 62))

        # level bar
        draw.rectangle([(105,140), (280,160)], fill=(255,255,255,255), outline=(255, 255, 255, 160)) # box

        # bar
        full_length = 278-107
        init_pos = 107
        level_length = int(full_length * (userinfo["current_exp"]/self.required_exp(userinfo["level"])))
        draw.rectangle([(init_pos, 142), (init_pos+level_length, 158)], fill=(150,150,150,255)) # box

        #divider bar
        draw.rectangle([(105, 213), (280, 215)], fill=(150,150,150,255)) # box

        # write label text
        white_color = (255,255,255,255)
        light_color = (100,100,100,255)
        draw.text((110, 103), u"{}".format(userinfo["name"]),  font=name_fnt, fill=white_color) # Name
        draw.text((110, 118), u"{}".format(userinfo["title"]), font=title_fnt, fill=white_color) # Title

        rep_text = "+{}rep".format(userinfo["rep"])
        draw.text((self.center(5, 100, rep_text, rep_fnt), 143), rep_text, font=rep_fnt, fill=white_color)

        draw.text((self.center(5, 100, "Badges", sub_header_fnt), 175), "Badges", font=sub_header_fnt, fill=white_color) # Badges   


        exp_text = "Exp: {}/{}".format(userinfo["current_exp"],self.required_exp(userinfo["level"]))
        draw.text((self.center(init_pos, 278, exp_text, exp_fnt), 145), exp_text,  font=exp_fnt, fill=(40,40,40,250)) # Exp Bar
        
        lvl_left = 106
        draw.text((lvl_left, 165), "Level",  font=level_label_fnt, fill=light_color) # Level Label
        lvl_label_width = level_label_fnt.getsize("Level")[0]
        lvl_txt = "{}".format(userinfo["level"])
        draw.text((self.center(lvl_left, lvl_left+lvl_label_width, lvl_txt, level_fnt), 183), lvl_txt,  font=level_fnt, fill=light_color) # Level #

        label_align = 150
        draw.text((label_align, 165), "Total Exp:",  font=sub_header_fnt, fill=light_color) # Exp
        draw.text((label_align, 180), "Server Rank:", font=sub_header_fnt, fill=light_color) # Server Rank
        draw.text((label_align, 195), "Credits:",  font=sub_header_fnt, fill=light_color) # Credits

        num_align = 230
        draw.text((num_align, 165), "{}".format(userinfo["total_exp"]),  font=sub_header_fnt, fill=light_color) # Exp
        draw.text((num_align, 180), "#{}".format(await self.find_rank(user, server)), font=sub_header_fnt, fill=light_color) # Server Rank
        try:
            credits = fileIO("data/economy/bank.json", "load")[server.id][user.id]["balance"]
        except:
            credits = 0
        draw.text((num_align, 195), "${}".format(credits),  font=sub_header_fnt, fill=light_color) # Credits

        draw.text((105, 220), "Info Box",  font=sub_header_fnt, fill=white_color) # Info Box 
        margin = 105
        offset = 238
        for line in textwrap.wrap(userinfo["info"], width=40):
            draw.text((margin, offset), line, font=text_fnt, fill=(70,70,70,255))
            offset += text_fnt.getsize(line)[1] + 2

        result = Image.alpha_composite(result, process)
        result.save('data/leveler/profile.png','PNG', quality=100)

        os.remove('data/leveler/temp_bg.png')
        os.remove('data/leveler/temp_profile.png')     
        os.remove('data/leveler/temp_discord_logo.png')
        os.remove('data/leveler/temp_info.png') 

    async def draw_rank(self, user, server):
        userinfo = self.users[server.id][user.id]
        # get urls
        bg_url = userinfo["rank_background"]
        profile_url = user.avatar_url         

        # create image objects
        bg_image = Image
        profile_image = Image      
    
        async with aiohttp.get(bg_url) as r:
            image = await r.content.read()
        with open('data/leveler/temp_bg.png','wb') as f:
            f.write(image)
        async with aiohttp.get(profile_url) as r:
            image = await r.content.read()
        with open('data/leveler/temp_profile.png','wb') as f:
            f.write(image)

        bg_image = Image.open('data/leveler/temp_bg.png').convert('RGBA')            
        profile_image = Image.open('data/leveler/temp_profile.png').convert('RGBA')

        # set canvas
        bg_color = (255,255,255, 0)
        result = Image.new('RGBA', (360, 100), bg_color)
        process = Image.new('RGBA', (360, 100), bg_color)
        # puts in background
        result.paste(bg_image, (0,0))

        # draw
        draw = ImageDraw.Draw(process)

        # draw transparent overlay           
        draw.rectangle([(77,5), (355, 95)], fill=(200,200,200,230)) # box
        draw.rectangle([(37,12), (113,89)], fill=(255,255,255, 160), outline=(100, 100, 100, 100)) # profile square

        # put in profile picture
        profile_size = (74, 74)
        profile_image = profile_image.resize(profile_size, Image.ANTIALIAS)
        process.paste(profile_image, (39, 14))

        # level bar
        draw.rectangle([(140,28), (330,45)], fill=(255,255,255,255), outline=(255, 255, 255, 160)) # box
        # actual bar
        full_length = 328 - 142
        init_pos = 142
        level_length = int(full_length * (userinfo["current_exp"]/self.required_exp(userinfo["level"])))    
        draw.rectangle([(init_pos,30), (init_pos+level_length, 43)], fill=(200,200,200,250)) # box    

        # write label text    
        draw.text((140, 10), u"{}".format(userinfo["name"]),  font=name_fnt, fill=(110,110,110,255)) # Name
        exp_text = "Exp: {}/{}".format(userinfo["current_exp"],self.required_exp(userinfo["level"]))
        draw.text((self.center(140, 330, exp_text, exp_fnt), 31), exp_text,  font=exp_fnt, fill=(70,70,70,230)) # Exp Bar
        
        lvl_align = 142
        draw.text((lvl_align, 50), "Level",  font=level_label_fnt, fill=(110,110,110,255)) # Level Label
        lvl_label_width = level_label_fnt.getsize("Level")[0]
        lvl_text = "{}".format(userinfo["level"])
        draw.text((self.center(lvl_align, lvl_align + lvl_label_width, lvl_text, level_fnt), 68), lvl_text,  font=level_fnt, fill=(110,110,110,255)) # Level #

        # divider bar
        draw.rectangle([(190,50), (191, 90)], fill=(110,110,110,240))      

        label_align = 210
        draw.text((label_align, 55), "Server Rank:", font=sub_header_fnt, fill=(110,110,110,255)) # Server Rank Label
        draw.text((label_align, 75), "Credits:",  font=sub_header_fnt, fill=(110,110,110,255)) # Credits

        text_align = 290
        draw.text((text_align, 55), "#{}".format(await self.find_rank(user, server)), font=sub_header_fnt, fill=(110,110,110,255)) # Server Rank
        try:
            credits = fileIO("data/economy/bank.json", "load")[server.id][user.id]["balance"]
        except:
            credits = 0
        draw.text((text_align, 75), "${}".format(credits),  font=sub_header_fnt, fill=(110,110,110,255)) # Credits

        result = Image.alpha_composite(result, process)
        result.save('data/leveler/rank.png','PNG', quality=100)

        os.remove('data/leveler/temp_bg.png')
        os.remove('data/leveler/temp_profile.png')

    """
    @commands.command(pass_context=True, no_pm=True)
    async def lvltest(self,ctx,user : discord.Member=None):
        '''Displays the rank of a user.'''
        if user == None:
            user = ctx.message.author
        channel = ctx.message.channel
        server = user.server

        # get urls
        await self.draw_levelup(user, server)
        await self.bot.send_typing(channel)            
        await self.bot.send_file(channel, 'data/leveler/level.png')"""

    async def draw_levelup(self, user, server):
        userinfo = self.users[server.id][user.id]
        # get urls
        bg_url = userinfo["levelup_background"]
        profile_url = user.avatar_url         

        # create image objects
        bg_image = Image
        profile_image = Image   
    
        async with aiohttp.get(bg_url) as r:
            image = await r.content.read()
        with open('data/leveler/temp_bg.png','wb') as f:
            f.write(image)
        async with aiohttp.get(profile_url) as r:
            image = await r.content.read()
        with open('data/leveler/temp_profile.png','wb') as f:
            f.write(image)

        bg_image = Image.open('data/leveler/temp_bg.png').convert('RGBA')            
        profile_image = Image.open('data/leveler/temp_profile.png').convert('RGBA')

        # set canvas
        bg_color = (255,255,255, 0)
        result = Image.new('RGBA', (85, 105), bg_color)
        process = Image.new('RGBA', (85, 105), bg_color)

        # draw
        draw = ImageDraw.Draw(process)

        # puts in background
        result.paste(bg_image, (0,0))

        # draw transparent overlay           
        draw.rectangle([(0, 40), (85, 105)], fill=(200,200,200,200)) # white portion
        draw.rectangle([(15, 11), (68, 63)], fill=(255,255,255,160), outline=(100, 100, 100, 100)) # profile rectangle

        # put in profile picture
        profile_size = (50, 50)
        profile_image = profile_image.resize(profile_size, Image.ANTIALIAS)
        process.paste(profile_image, (17, 13))

        # fonts
        level_fnt2 = ImageFont.truetype('data/leveler/fonts/font_bold.ttf', 20)
        level_fnt = ImageFont.truetype('data/leveler/fonts/font_bold.ttf', 32)

        # write label text
        draw.text((self.center(0, 85, "Level Up!", level_fnt2), 65), "Level Up!", font=level_fnt2, fill=(100,100,100,250)) # Level
        lvl_text = "{}".format(userinfo["level"])
        draw.text((self.center(0, 85, lvl_text, level_fnt), 80), lvl_text, font=level_fnt, fill=(100,100,100,250)) # Level Number

        result = Image.alpha_composite(result, process)
        result.save('data/leveler/level.png','PNG', quality=100)

        os.remove('data/leveler/temp_bg.png')
        os.remove('data/leveler/temp_profile.png') 

    # loads the new text into the model
    async def on_message(self, message):
        text = message.content
        server = message.author.server
        channel = message.channel
        user = message.author
        curr_time = time.time()

        if user.bot:
            return

        if server.id not in self.users:
            self.users[server.id] = {}
        if user.id not in self.users[server.id]:
            new_account = {
                "name": user.name,
                "level": 0,
                "current_exp": 0,
                "total_exp": 0,
                "profile_background": 'http://tatsumaki.xyz/images/backgrounds/profile/iceberg_prof_bg.png',
                "rank_background": 'http://tatsumaki.xyz/images/backgrounds/rank/tri_rainbow_rank_bg.png',
                "levelup_background": 'http://tatsumaki.xyz/images/backgrounds/levelup/default_lvlup_bg.png',
                "title": "",
                "info": "I am a mysterious person.",
                "rep": 0,
                "badges":[]
            }
            self.users[server.id][user.id] = new_account

        if server.id not in self.block:
            self.block[server.id] = {}
            fileIO('data/leveler/block.json', "save", self.block)
        if user.id not in self.block[server.id]:
            self.block[server.id][user.id] = {
                "chat": time.time(),
                "rep" : time.time()
            }
            fileIO('data/leveler/block.json', "save", self.block)

        if float(curr_time) - float(self.block[server.id][user.id]["chat"]) >= 60 and prefix not in text:
            await self.process_exp(message, random.randint(15, 20))
            self.block[server.id][user.id]["chat"] = time.time()
            fileIO('data/leveler/block.json', "save", self.block)

        fileIO('data/leveler/users.json', "save", self.users)

    async def process_exp(self, message, exp:int):
        server = message.author.server
        channel = message.channel
        user = message.author

        required = self.required_exp(self.users[server.id][user.id]["level"])

        self.users[server.id][user.id]["total_exp"] += exp
        if self.users[server.id][user.id]["current_exp"] + exp >= required:
            self.users[server.id][user.id]["level"] += 1
            self.users[server.id][user.id]["current_exp"] = self.users[server.id][user.id]["current_exp"] + exp - required
            await self.draw_levelup(user, server)
            await self.bot.send_typing(channel)           
            await self.bot.send_file(channel, 'data/leveler/level.png', content='**{} just gained a level!**'.format(user.mention)) 
        else:
            self.users[server.id][user.id]["current_exp"] += exp

    async def find_rank(self, user, server):
        userinfo = self.users[server.id]
        targetid = user.id

        users = []
        for userkey in userinfo.keys():
            users.append((userkey, userinfo[userkey]["name"], userinfo[userkey]["total_exp"]))
        sorted_list = sorted(users, key=operator.itemgetter(2), reverse=True)

        rank = 1
        for user in sorted_list:
            if user[0] == targetid:
                return rank
            rank+=1

    # finds the the pixel to center the text
    def center(self, start, end, text, font):
        dist = end - start
        width = font.getsize(text)[0]
        start_pos = start + ((dist-width)/2)
        return int(start_pos)

    # calculates required exp for next level
    def required_exp(self, level:int):
        return 139*level+65
# ------------------------------ setup ----------------------------------------    
def check_folders():
    if not os.path.exists("data/leveler"):
        print("Creating data/leveler folder...")
        os.makedirs("data/leveler")

def check_files():
    f = "data/leveler/users.json"
    if not fileIO(f, "check"):
        print("Creating users.json...")
        fileIO(f, "save", {})

    f = "data/leveler/block.json"
    if not fileIO(f, "check"):
        print("Creating block.json...")
        fileIO(f, "save", {})

def setup(bot):
    check_folders()
    check_files()

    if pil_available is False:
        raise RuntimeError("You don't have Pillow installed, run\n```pip3 install pillow```And try again")
        return

    n = Leveler(bot)
    bot.add_listener(n.on_message,"on_message")
    bot.add_cog(n)
