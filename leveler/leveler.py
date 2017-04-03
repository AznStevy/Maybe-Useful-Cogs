import discord
from discord.ext import commands
from discord.utils import find
from .utils.chat_formatting import pagify
from __main__ import send_cmd_help
import platform, asyncio, string, operator, random, textwrap
import os, re, aiohttp
from .utils.dataIO import fileIO
from cogs.utils import checks
try:
    from pymongo import MongoClient
except:
    raise RuntimeError("Can't load pymongo. Do 'pip3 install pymongo'.")
try:
    import scipy
    import scipy.misc
    import scipy.cluster
except:
    pass
try:
    from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageOps
except:
    raise RuntimeError("Can't load pillow. Do 'pip3 install pillow'.")
import time

# fonts
font_file = 'data/leveler/fonts/font.ttf'
font_bold_file = 'data/leveler/fonts/font_bold.ttf'
font_unicode_file = 'data/leveler/fonts/unicode.ttf'

# Credits (None)
bg_credits = {

}

# directory
user_directory = "data/leveler/users"

prefix = fileIO("data/red/settings.json", "load")['PREFIXES']
default_avatar_url = "http://i.imgur.com/XPDO9VH.jpg"

try:
    client = MongoClient()
    db = client['leveler']
except:
    print("Can't load database. Follow instructions on Git/online to install MongoDB.")

class Leveler:
    """A level up thing with image generation!"""

    def __init__(self, bot):
        self.bot = bot
        self.backgrounds = fileIO("data/leveler/backgrounds.json", "load")
        self.badges = fileIO("data/leveler/badges.json", "load")
        self.settings = fileIO("data/leveler/settings.json", "load")
        bot_settings = fileIO("data/red/settings.json", "load")
        self.owner = bot_settings["OWNER"]

        dbs = client.database_names()
        if 'leveler' not in dbs:
            self.pop_database()

    def pop_database(self):
        if os.path.exists("data/leveler/users"):
            for userid in os.listdir(user_directory):
                userinfo = fileIO("data/leveler/users/{}/info.json".format(userid), "load")
                userinfo['user_id'] = userid
                db.users.insert_one(userinfo)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(name = "profile", pass_context=True, no_pm=True)
    async def profile(self,ctx, *, user : discord.Member=None):
        """Displays a user profile."""
        if user == None:
            user = ctx.message.author
        channel = ctx.message.channel
        server = user.server
        curr_time = time.time()

        # creates user if doesn't exist
        await self._create_user(user, server)
        userinfo = db.users.find_one({'user_id':user.id})

        # check if disabled
        if server.id in self.settings["disabled_servers"]:
            await self.bot.say("**Leveler commands for this server are disabled!**")
            return

        # no cooldown for text only
        if "text_only" in self.settings and server.id in self.settings["text_only"]:
            em = await self.profile_text(user, server, userinfo)
            await self.bot.send_message(channel, '', embed = em)
        else:
            await self.draw_profile(user, server)
            await self.bot.send_typing(channel)
            await self.bot.send_file(channel, 'data/leveler/temp/{}_profile.png'.format(user.id), content='**User profile for {}**'.format(self._is_mention(user)))
            db.users.update_one({'user_id':user.id}, {'$set':{
                    "profile_block": curr_time,
                }}, upsert = True)
            try:
                os.remove('data/leveler/temp/{}_profile.png'.format(user.id))
            except:
                pass

    async def profile_text(self, user, server, userinfo):
        def test_empty(text):
            if text == '':
                return "None"
            else:
                return text

        em = discord.Embed(description='', colour=user.colour)
        em.add_field(name="Title:", value = test_empty(userinfo["title"]))
        em.add_field(name="Reps:", value= userinfo["rep"])
        em.add_field(name="Global Rank:", value = '#{}'.format(await self._find_global_rank(user, server)))
        em.add_field(name="Server Rank:", value = '#{}'.format(await self._find_server_rank(user, server)))
        em.add_field(name="Server Level:", value = format(userinfo["servers"][server.id]["level"]))
        em.add_field(name="Total Exp:", value = userinfo["total_exp"])
        em.add_field(name="Server Exp:", value = await self._find_server_exp(user, server))
        try:
            bank = self.bot.get_cog('Economy').bank
            if bank.account_exists(user):
                credits = bank.get_balance(user)
            else:
                credits = 0
        except:
            credits = 0
        em.add_field(name="Credits: ", value = "${}".format(credits))
        em.add_field(name="Info: ", value = test_empty(userinfo["info"]))
        em.add_field(name="Badges: ", value = test_empty(", ".join(userinfo["badges"])).replace("_", " "))
        em.set_author(name="Profile for {}".format(user.name), url = user.avatar_url)
        em.set_thumbnail(url=user.avatar_url)
        return em

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(pass_context=True, no_pm=True)
    async def rank(self,ctx,user : discord.Member=None):
        """Displays the rank of a user."""
        if user == None:
            user = ctx.message.author
        channel = ctx.message.channel
        server = user.server
        curr_time = time.time()

        # creates user if doesn't exist
        await self._create_user(user, server)
        userinfo = db.users.find_one({'user_id':user.id})

        # check if disabled
        if server.id in self.settings["disabled_servers"]:
            await self.bot.say("**Leveler commands for this server are disabled!**")
            return

        # no cooldown for text only
        if "text_only" in self.settings and server.id in self.settings["text_only"]:
            em = await self.rank_text(user, server, userinfo)
            await self.bot.send_message(channel, '', embed = em)
        else:
            await self.draw_rank(user, server)
            await self.bot.send_typing(channel)
            await self.bot.send_file(channel, 'data/leveler/temp/{}_rank.png'.format(user.id), content='**Ranking & Statistics for {}**'.format(self._is_mention(user)))
            db.users.update_one({'user_id':user.id}, {'$set':{
                    "rank_block".format(server.id): curr_time,
                }}, upsert = True)
            try:
                os.remove('data/leveler/temp/{}_rank.png'.format(user.id))
            except:
                pass

    async def rank_text(self, user, server, userinfo):
        em = discord.Embed(description='', colour=user.colour)
        em.add_field(name="Server Rank", value = '#{}'.format(await self._find_server_rank(user, server)))
        em.add_field(name="Reps", value = userinfo["rep"])
        em.add_field(name="Server Level", value = userinfo["servers"][server.id]["level"])
        em.add_field(name="Server Exp", value = await self._find_server_exp(user, server))
        em.set_author(name="Rank and Statistics for {}".format(user.name), url = user.avatar_url)
        em.set_thumbnail(url=user.avatar_url)
        return em

    # should the user be mentioned based on settings?
    def _is_mention(self,user):
        if "mention" not in self.settings.keys() or self.settings["mention"]:
            return user.mention
        else:
            return user.name

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(pass_context=True, no_pm=True)
    async def top10(self,ctx, global_rank:str = None):
        '''Displays leaderboard. Add "global" parameter for global'''
        server = ctx.message.server

        if server.id in self.settings["disabled_servers"]:
            await self.bot.say("**Leveler commands for this server are disabled!**")
            return

        users = []
        if global_rank == "global":
            msg = "**Global Leaderboard for {}**\n".format(self.bot.user.name)
            # this is also terrible...
            for userinfo in db.users.find({}):
                try:
                    userid = userinfo['user_id']
                    for server in self.bot.servers:
                        temp_user = find(lambda m: m.id == userid, server.members)
                        if temp_user != None:
                            break
                    if temp_user != None:
                        users.append((temp_user.name, userinfo["total_exp"]))
                except:
                    pass
            sorted_list = sorted(users, key=operator.itemgetter(1), reverse=True)
        else:
            msg = "**Leaderboard for {}**\n".format(server.name)
            for userinfo in db.users.find({}):
                try:
                    userid = userinfo["user_id"]
                    if "servers" in userinfo and server.id in userinfo["servers"]:
                        temp_user = find(lambda m: m.id == userid, server.members)
                        server_exp = 0
                        for i in range(userinfo["servers"][server.id]["level"]):
                            server_exp += self._required_exp(i)
                        server_exp +=  userinfo["servers"][server.id]["current_exp"]
                        if temp_user != None:
                            users.append((temp_user.name, server_exp))
                except:
                    pass
            sorted_list = sorted(users, key=operator.itemgetter(1), reverse=True)

        msg += "```ruby\n"
        rank = 1
        labels = ["♔", "♕", "♖", "♗", "♘", "♙", "   ", "   ", "   ", "   "]
        for user in sorted_list[:10]:
            msg += u'{:<2}{:<2}{:<2}   # {:<5}\n'.format(rank, labels[rank-1], u"➤", user[0])
            msg += u'{:<2}{:<2}{:<2}    {:<5}\n'.format(" ", " ", " ", "Total Points: " + str(user[1]))
            rank += 1
        msg +="```"
        await self.bot.say(msg)

    @commands.command(pass_context=True, no_pm=True)
    async def rep(self, ctx, user : discord.Member):
        """Gives a reputation point to a designated player."""
        channel = ctx.message.channel
        server = user.server
        org_user = ctx.message.author
        # creates user if doesn't exist
        await self._create_user(org_user, server)
        await self._create_user(user, server)
        org_userinfo = db.users.find_one({'user_id':org_user.id})
        curr_time = time.time()

        if server.id in self.settings["disabled_servers"]:
            await self.bot.say("**Leveler commands for this server are disabled!**")
            return
        if user.id == org_user.id:
            await self.bot.say("**You can't give a rep to yourself!**")
            return
        if user.bot:
            await self.bot.say("**You can't give a rep to a bot!**")
            return
        if "rep_block" not in org_userinfo:
            org_userinfo["rep_block"] = 0

        delta = float(curr_time) - float(org_userinfo["rep_block"])
        if delta >= 43200.0 and delta>0:
            userinfo = db.users.find_one({'user_id':user.id})
            db.users.update_one({'user_id':org_user.id}, {'$set':{
                    "rep_block": curr_time,
                }})
            db.users.update_one({'user_id':user.id}, {'$set':{
                    "rep":  userinfo["rep"] + 1,
                }})
            await self.bot.say("**You have just given {} a reputation point!**".format(self._is_mention(user)))
        else:
            # calulate time left
            seconds = 43200 - delta
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            await self.bot.say("**You need to wait {} hours, {} minutes, and {} seconds until you can give reputation again!**".format(int(h), int(m), int(s)))

    @commands.command(pass_context=True, no_pm=True)
    async def lvlinfo(self, ctx, user : discord.Member = None):
        """Gives more specific details about user profile image."""

        if not user:
            user = ctx.message.author
        server = ctx.message.server
        userinfo = db.users.find_one({'user_id':user.id})

        server = ctx.message.server

        if server.id in self.settings["disabled_servers"]:
            await self.bot.say("**Leveler commands for this server are disabled!**")
            return

        # creates user if doesn't exist
        await self._create_user(user, server)
        msg = ""
        msg += "Name: {}\n".format(user.name)
        msg += "Title: {}\n".format(userinfo["title"])
        msg += "Reps: {}\n".format(userinfo["rep"])
        msg += "Server Level: {}\n".format(userinfo["servers"][server.id]["level"])
        total_server_exp = 0
        for i in range(userinfo["servers"][server.id]["level"]):
            total_server_exp += self._required_exp(i)
        total_server_exp += userinfo["servers"][server.id]["current_exp"]
        msg += "Server Exp: {}\n".format(total_server_exp)
        msg += "Total Exp: {}\n".format(userinfo["total_exp"])
        msg += "Info: {}\n".format(userinfo["info"])
        msg += "Profile background: {}\n".format(userinfo["profile_background"])
        msg += "Rank background: {}\n".format(userinfo["rank_background"])
        msg += "Levelup background: {}\n".format(userinfo["levelup_background"])
        if "profile_info_color" in userinfo.keys() and userinfo["profile_info_color"]:
            msg += "Profile info color: {}\n".format(self._rgb_to_hex(userinfo["profile_info_color"]))
        if "profile_exp_color" in userinfo.keys() and userinfo["profile_exp_color"]:
            msg += "Profile exp color: {}\n".format(self._rgb_to_hex(userinfo["profile_exp_color"]))
        if "rep_color" in userinfo.keys() and userinfo["rep_color"]:
            msg += "Rep section color: {}\n".format(self._rgb_to_hex(userinfo["rep_color"]))
        if "badge_col_color" in userinfo.keys() and userinfo["badge_col_color"]:
            msg += "Badge section color: {}\n".format(self._rgb_to_hex(userinfo["badge_col_color"]))
        if "rank_info_color" in userinfo.keys() and userinfo["rank_info_color"]:
            msg += "Rank info color: {}\n".format(self._rgb_to_hex(userinfo["rank_info_color"]))
        if "rank_exp_color" in userinfo.keys() and userinfo["rank_exp_color"]:
            msg += "Rank exp color: {}\n".format(self._rgb_to_hex(userinfo["rank_exp_color"]))
        if "levelup_info_color" in userinfo.keys() and userinfo["levelup_info_color"]:
            msg += "Level info color: {}\n".format(self._rgb_to_hex(userinfo["levelup_info_color"]))
        msg += "Badges: "
        msg += ", ".join(userinfo["badges"])

        em = discord.Embed(description=msg, colour=user.colour)
        em.set_author(name="Profile Information for {}".format(user.name), icon_url = user.avatar_url)
        await self.bot.say(embed = em)

    def _rgb_to_hex(self, rgb):
        rgb = tuple(rgb[:3])
        return '#%02x%02x%02x' % rgb

    @commands.group(name = "lvlset", pass_context=True)
    async def lvlset(self, ctx):
        """Profile Configuration Options"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            return

    @lvlset.group(name = "profile", pass_context=True)
    async def profileset(self, ctx):
        """Profile options"""
        if ctx.invoked_subcommand is None or \
                isinstance(ctx.invoked_subcommand, commands.Group):
            await send_cmd_help(ctx)
            return

    @lvlset.group(name = "rank", pass_context=True)
    async def rankset(self, ctx):
        """Rank options"""
        if ctx.invoked_subcommand is None or \
                isinstance(ctx.invoked_subcommand, commands.Group):
            await send_cmd_help(ctx)
            return

    @lvlset.group(name = "levelup", pass_context=True)
    async def levelupset(self, ctx):
        """Level-Up options"""
        if ctx.invoked_subcommand is None or \
                isinstance(ctx.invoked_subcommand, commands.Group):
            await send_cmd_help(ctx)
            return

    @profileset.command(name = "color", pass_context=True, no_pm=True)
    async def profilecolors(self, ctx, section:str, color:str):
        """Set info color. e.g [p]lvlset profile color [exp|rep|badge|info|all] [default|white|hex|auto]"""
        user = ctx.message.author
        server = ctx.message.server
        # creates user if doesn't exist
        await self._create_user(user, server)
        userinfo = db.users.find_one({'user_id':user.id})

        section = section.lower()
        default_info_color = (30, 30 ,30, 200)
        white_info_color = (150, 150, 150, 180)
        default_rep = (92,130,203,230)
        default_badge = (128,151,165,230)
        default_exp = (255, 255, 255, 230)
        default_a = 200

        if server.id in self.settings["disabled_servers"]:
            await self.bot.say("**Leveler commands for this server are disabled!**")
            return

        if "text_only" in self.settings and server.id in self.settings["text_only"]:
            await self.bot.say("**Text-only commands allowed.**")
            return

        # get correct section for db query
        if section == "rep":
            section_name = "rep_color"
        elif section == "exp":
            section_name = "profile_exp_color"
        elif section == "badge":
            section_name = "badge_col_color"
        elif section == "info":
            section_name = "profile_info_color"
        elif section == "all":
            section_name = "all"
        else:
            await self.bot.say("**Not a valid section. (rep, exp, badge, info, all)**")
            return

        # get correct color choice
        if color == "auto":
            if section == "exp":
                color_ranks = [random.randint(2,3)]
            elif section == "rep":
                color_ranks = [random.randint(2,3)]
            elif section == "badge":
                color_ranks = [0] # most prominent color
            elif section == "info":
                color_ranks = [random.randint(0,1)]
            elif section == "all":
                color_ranks = [random.randint(2,3), random.randint(2,3), 0, random.randint(0,2)]

            hex_colors = await self._auto_color(userinfo["profile_background"], color_ranks)
            set_color = []
            for hex_color in hex_colors:
                color_temp = self._hex_to_rgb(hex_color, default_a)
                set_color.append(color_temp)

        elif color == "white":
            set_color = [white_info_color]
        elif color == "default":
            if section == "exp":
                set_color = [default_exp]
            elif section == "rep":
                set_color = [default_rep]
            elif section == "badge":
                set_color = [default_badge]
            elif section == "info":
                set_color = [default_info_color]
            elif section == "all":
                set_color = [default_exp, default_rep, default_badge, default_info_color]
        elif self._is_hex(color):
            set_color = [self._hex_to_rgb(color, default_a)]
        else:
            await self.bot.say("**Not a valid color. (default, hex, white, auto)**")
            return

        if section == "all":
            if len(set_color) == 1:
                db.users.update_one({'user_id':user.id}, {'$set':{
                        "profile_exp_color": set_color[0],
                        "rep_color": set_color[0],
                        "badge_col_color": set_color[0],
                        "profile_info_color": set_color[0]
                    }})
            elif color == "default":
                db.users.update_one({'user_id':user.id}, {'$set':{
                        "profile_exp_color": default_exp,
                        "rep_color": default_rep,
                        "badge_col_color": default_badge,
                        "profile_info_color": default_info_color
                    }})
            elif color == "auto":
                db.users.update_one({'user_id':user.id}, {'$set':{
                        "profile_exp_color": set_color[0],
                        "rep_color": set_color[1],
                        "badge_col_color": set_color[2],
                        "profile_info_color": set_color[3]
                    }})
            await self.bot.say("**Colors for profile set.**")
        else:
            print("update one")
            db.users.update_one({'user_id':user.id}, {'$set':{
                    section_name: set_color[0]
                }})
            await self.bot.say("**Color for profile {} set.**".format(section))

    @rankset.command(name = "color", pass_context=True, no_pm=True)
    async def rankcolors(self, ctx, section:str, color:str = None):
        """Set info color. e.g [p]lvlset rank color [exp|info] [default|white|hex|auto]"""
        user = ctx.message.author
        server = ctx.message.server
        # creates user if doesn't exist
        await self._create_user(user, server)
        userinfo = db.users.find_one({'user_id':user.id})

        section = section.lower()
        default_info_color = (30, 30 ,30, 200)
        white_info_color = (150, 150, 150, 180)
        default_exp = (255, 255, 255, 230)
        default_a = 200

        if server.id in self.settings["disabled_servers"]:
            await self.bot.say("**Leveler commands for this server are disabled!**")
            return

        if "text_only" in self.settings and server.id in self.settings["text_only"]:
            await self.bot.say("**Text-only commands allowed.**")
            return

        # get correct section for db query
        if section == "exp":
            section_name = "rank_exp_color"
        elif section == "info":
            section_name = "rank_info_color"
        elif section == "all":
            section_name = "all"
        else:
            await self.bot.say("**Not a valid section. (exp, info, all)**")
            return

        # get correct color choice
        if color == "auto":
            if section == "exp":
                color_ranks = [random.randint(2,3)]
            elif section == "info":
                color_ranks = [random.randint(0,1)]
            elif section == "all":
                color_ranks = [random.randint(2,3), random.randint(0,1)]

            hex_colors = await self._auto_color(userinfo["rank_background"], color_ranks)
            set_color = []
            for hex_color in hex_colors:
                color_temp = self._hex_to_rgb(hex_color, default_a)
                set_color.append(color_temp)
        elif color == "white":
            set_color = [white_info_color]
        elif color == "default":
            if section == "exp":
                set_color = [default_exp]
            elif section == "info":
                set_color = [default_info_color]
            elif section == "all":
                set_color = [default_exp, default_rep, default_badge, default_info_color]
        elif self._is_hex(color):
            set_color = [self._hex_to_rgb(color, default_a)]
        else:
            await self.bot.say("**Not a valid color. (default, hex, white, auto)**")
            return

        if section == "all":
            if len(set_color) == 1:
                db.users.update_one({'user_id':user.id}, {'$set':{
                        "rank_exp_color": set_color[0],
                        "rank_info_color": set_color[0]
                    }})
            elif color == "default":
                db.users.update_one({'user_id':user.id}, {'$set':{
                        "rank_exp_color": default_exp,
                        "rank_info_color": default_info_color
                    }})
            elif color == "auto":
                db.users.update_one({'user_id':user.id}, {'$set':{
                        "rank_exp_color": set_color[0],
                        "rank_info_color": set_color[1]
                    }})
            await self.bot.say("**Colors for rank set.**")
        else:
            db.users.update_one({'user_id':user.id}, {'$set':{
                    section_name: set_color[0]
                }})
            await self.bot.say("**Color for rank {} set.**".format(section))

    @levelupset.command(name = "color", pass_context=True, no_pm=True)
    async def levelupcolors(self, ctx, section:str, color:str = None):
        """Set info color. e.g [p]lvlset color [info] [default|white|hex|auto]"""
        user = ctx.message.author
        server = ctx.message.server
        # creates user if doesn't exist
        await self._create_user(user, server)
        userinfo = db.users.find_one({'user_id':user.id})

        section = section.lower()
        default_info_color = (30, 30 ,30, 200)
        white_info_color = (150, 150, 150, 180)
        default_a = 200

        if server.id in self.settings["disabled_servers"]:
            await self.bot.say("**Leveler commands for this server are disabled!**")
            return

        if "text_only" in self.settings and server.id in self.settings["text_only"]:
            await self.bot.say("**Text-only commands allowed.**")
            return

        # get correct section for db query
        if section == "info":
            section_name = "levelup_info_color"
        else:
            await self.bot.say("**Not a valid section. (info)**")
            return

        # get correct color choice
        if color == "auto":
            if section == "info":
                color_ranks = [random.randint(0,1)]
            hex_colors = await self._auto_color(userinfo["levelup_background"], color_ranks)
            set_color = []
            for hex_color in hex_colors:
                color_temp = self._hex_to_rgb(hex_color, default_a)
                set_color.append(color_temp)
        elif color == "white":
            set_color = [white_info_color]
        elif color == "default":
            if section == "info":
                set_color = [default_info_color]
        elif self._is_hex(color):
            set_color = [self._hex_to_rgb(color, default_a)]
        else:
            await self.bot.say("**Not a valid color. (default, hex, white, auto)**")
            return

        db.users.update_one({'user_id':user.id}, {'$set':{
                section_name: set_color[0]
            }})
        await self.bot.say("**Color for level-up {} set.**".format(section))

    # uses k-means algorithm to find color from bg, rank is abundance of color, descending
    async def _auto_color(self, url:str, ranks):
        phrases = ["Calculating colors..."] # in case I want more
        #try:
        await self.bot.say("**{}**".format(random.choice(phrases)))
        clusters = 10

        async with aiohttp.get(url) as r:
            image = await r.content.read()
        with open('data/leveler/temp_auto.png','wb') as f:
            f.write(image)

        im = Image.open('data/leveler/temp_auto.png').convert('RGBA')
        im = im.resize((290, 290)) # resized to reduce time
        ar = scipy.misc.fromimage(im)
        shape = ar.shape
        ar = ar.reshape(scipy.product(shape[:2]), shape[2])

        codes, dist = scipy.cluster.vq.kmeans(ar.astype(float), clusters)
        vecs, dist = scipy.cluster.vq.vq(ar, codes)         # assign codes
        counts, bins = scipy.histogram(vecs, len(codes))    # count occurrences

        # sort counts
        freq_index = []
        index = 0
        for count in counts:
            freq_index.append((index, count))
            index += 1
        sorted_list = sorted(freq_index, key=operator.itemgetter(1), reverse=True)

        colors = []
        for rank in ranks:
            color_index = min(rank, len(codes))
            peak = codes[sorted_list[color_index][0]] # gets the original index
            peak = peak.astype(int)

            colors.append(''.join(format(c, '02x') for c in peak))
        return colors # returns array
        #except:
            #await self.bot.say("```Error or no scipy. Install scipy doing 'pip3 install numpy' and 'pip3 install scipy' or read here: https://github.com/AznStevy/Maybe-Useful-Cogs/blob/master/README.md```")

    # converts hex to rgb
    def _hex_to_rgb(self, hex_num: str, a:int):
        h = hex_num.lstrip('#')

        # if only 3 characters are given
        if len(str(h)) == 3:
            expand = ''.join([x*2 for x in str(h)])
            h = expand

        colors = [int(h[i:i+2], 16) for i in (0, 2 ,4)]
        colors.append(a)
        return tuple(colors)

    # dampens the color given a parameter
    def _moderate_color(self, rgb, a, moderate_num):
        new_colors = []
        for color in rgb[:3]:
            if color > 128:
                color -= moderate_num
            else:
                color += moderate_num
            new_colors.append(color)
        new_colors.append(230)

        return tuple(new_colors)


    @profileset.command(pass_context=True, no_pm=True)
    async def info(self, ctx, *, info):
        """Set your user info."""
        user = ctx.message.author
        server = ctx.message.server
        # creates user if doesn't exist
        await self._create_user(user, server)
        userinfo = db.users.find_one({'user_id':user.id})
        max_char = 150

        if server.id in self.settings["disabled_servers"]:
            await self.bot.say("Leveler commands for this server are disabled.")
            return

        if len(info) < max_char:
            db.users.update_one({'user_id':user.id}, {'$set':{"info": info}})
            await self.bot.say("**Your info section has been succesfully set!**")
        else:
            await self.bot.say("**Your description has too many characters! Must be <{}**".format(max_char))

    @levelupset.command(name = "bg", pass_context=True, no_pm=True)
    async def levelbg(self, ctx, *, image_name:str):
        """Set your level background"""
        user = ctx.message.author
        server = ctx.message.server
        # creates user if doesn't exist
        await self._create_user(user, server)
        userinfo = db.users.find_one({'user_id':user.id})

        if server.id in self.settings["disabled_servers"]:
            await self.bot.say("Leveler commands for this server are disabled.")
            return

        if "text_only" in self.settings and server.id in self.settings["text_only"]:
            await self.bot.say("**Text-only commands allowed.**")
            return


        if image_name in self.backgrounds["levelup"].keys():
            if await self._process_purchase(ctx):
                db.users.update_one({'user_id':user.id}, {'$set':{"levelup_background": self.backgrounds["levelup"][image_name]}})
                await self.bot.say("**Your new level-up background has been succesfully set!**")
        else:
            await self.bot.say("That is not a valid bg. See available bgs at `{}lvlbg list levelup`".format(prefix))

    @profileset.command(name = "bg", pass_context=True, no_pm=True)
    async def profilebg(self, ctx, *, image_name:str):
        """Set your profile background"""
        user = ctx.message.author
        server = ctx.message.server
        # creates user if doesn't exist
        await self._create_user(user, server)
        userinfo = db.users.find_one({'user_id':user.id})

        if server.id in self.settings["disabled_servers"]:
            await self.bot.say("Leveler commands for this server are disabled.")
            return

        if "text_only" in self.settings and server.id in self.settings["text_only"]:
            await self.bot.say("**Text-only commands allowed.**")
            return


        if image_name in self.backgrounds["profile"].keys():
            if await self._process_purchase(ctx):
                db.users.update_one({'user_id':user.id}, {'$set':{"profile_background": self.backgrounds["profile"][image_name]}})
                await self.bot.say("**Your new profile background has been succesfully set!**")
        else:
            await self.bot.say("That is not a valid bg. See available bgs at `{}lvlbg list profile`".format(prefix))

    @rankset.command(name = "bg", pass_context=True, no_pm=True)
    async def rankbg(self, ctx, *, image_name:str):
        """Set your rank background"""
        user = ctx.message.author
        server = ctx.message.server
        # creates user if doesn't exist
        await self._create_user(user, server)
        userinfo = db.users.find_one({'user_id':user.id})

        if server.id in self.settings["disabled_servers"]:
            await self.bot.say("Leveler commands for this server are disabled.")
            return

        if "text_only" in self.settings and server.id in self.settings["text_only"]:
            await self.bot.say("**Text-only commands allowed.**")
            return


        if image_name in self.backgrounds["rank"].keys():
            if await self._process_purchase(ctx):
                db.users.update_one({'user_id':user.id}, {'$set':{"rank_background": self.backgrounds["rank"][image_name]}})
                await self.bot.say("**Your new rank background has been succesfully set!**")
        else:
            await self.bot.say("That is not a valid bg. See available bgs at `{}lvlbg list rank`".format(prefix))

    @profileset.command(pass_context=True, no_pm=True)
    async def title(self, ctx, *, title):
        """Set your title."""
        user = ctx.message.author
        server = ctx.message.server
        # creates user if doesn't exist
        await self._create_user(user, server)
        userinfo = db.users.find_one({'user_id':user.id})
        max_char = 20

        if server.id in self.settings["disabled_servers"]:
            await self.bot.say("Leveler commands for this server are disabled.")
            return

        if len(title) < max_char:
            userinfo["title"] = title
            db.users.update_one({'user_id':user.id}, {'$set':{"title": title}})
            await self.bot.say("**Your title has been succesfully set!**")
        else:
            await self.bot.say("**Your title has too many characters! Must be <{}**".format(max_char))

    @checks.admin_or_permissions(manage_server=True)
    @commands.group(pass_context=True)
    async def lvladmin(self, ctx):
        """Admin Toggle Features"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            return

    @checks.admin_or_permissions(manage_server=True)
    @lvladmin.group(pass_context=True)
    async def overview(self, ctx):
        """A list of settings"""
        user = ctx.message.author

        disabled_servers = []
        private_levels = []
        disabled_levels = []
        locked_channels = []

        for server in self.bot.servers:
            if "disabled_servers" in self.settings.keys() and str(server.id) in self.settings["disabled_servers"]:
                disabled_servers.append(server.name)
            if "lvl_msg_lock" in self.settings.keys() and server.id in self.settings["lvl_msg_lock"].keys():
                for channel in server.channels:
                    if self.settings["lvl_msg_lock"][server.id] == channel.id:
                        locked_channels.append("\n{} → #{}".format(server.name,channel.name))
            if "lvl_msg" in self.settings.keys() and server.id in self.settings["lvl_msg"]:
                disabled_levels.append(server.name)
            if "private_lvl_msg" in self.settings.keys() and server.id in self.settings["private_lvl_msg"]:
                private_levels.append(server.name)

        num_users = 0
        for i in db.users.find({}):
            num_users += 1

        msg = ""
        msg += "**Servers:** {}\n".format(len(self.bot.servers))
        msg += "**Unique Users:** {}\n".format(num_users)
        if "mention" in self.settings.keys():
            msg += "**Mentions:** {}\n".format(str(self.settings["mention"]))
        msg += "**Background Price:** {}\n".format(self.settings["bg_price"])
        if "badge_type" in self.settings.keys():
            msg += "**Badge type:** {}\n".format(self.settings["badge_type"])
        msg += "**Disabled Servers:** {}\n".format(", ".join(disabled_servers))
        msg += "**Enabled Level Messages:** {}\n".format(", ".join(disabled_levels))
        msg += "**Private Level Messages:** {}\n".format(", ".join(private_levels))
        msg += "**Channel Locks:** {}\n".format(", ".join(locked_channels))
        em = discord.Embed(description=msg, colour=user.colour)
        em.set_author(name="Settings Overview for {}".format(self.bot.user.name))
        await self.bot.say(embed = em)

    @lvladmin.command(pass_context=True, no_pm=True)
    async def msgcredits(self, ctx, credits:int = 0):
        '''Credits per message logged. Default = 0'''
        channel = ctx.message.channel
        server = ctx.message.server

        if credits < 0 or credits > 1000:
            await self.bot.say("**Please enter a valid number (0 - 1000)**".format(channel.name))
            return

        if "msg_credits" not in self.settings.keys():
            self.settings["msg_credits"] = {}

        self.settings["msg_credits"][server.id] = credits
        await self.bot.say("**Credits per message logged set to `{}`.**".format(str(credits)))

        fileIO('data/leveler/settings.json', "save", self.settings)

    @lvladmin.command(name="lock", pass_context=True, no_pm=True)
    async def lvlmsglock(self, ctx):
        '''Locks levelup messages to one channel. Disable command via locked channel.'''
        channel = ctx.message.channel
        server = ctx.message.server

        if "lvl_msg_lock" not in self.settings.keys():
            self.settings["lvl_msg_lock"] = {}

        if server.id in self.settings["lvl_msg_lock"]:
            if channel.id == self.settings["lvl_msg_lock"][server.id]:
                del self.settings["lvl_msg_lock"][server.id]
                await self.bot.say("**Level-up message lock disabled.**".format(channel.name))
            else:
                self.settings["lvl_msg_lock"][server.id] = channel.id
                await self.bot.say("**Level-up message lock changed to `#{}`.**".format(channel.name))
        else:
            self.settings["lvl_msg_lock"][server.id] = channel.id
            await self.bot.say("**Level-up messages locked to `#{}`**".format(channel.name))

        fileIO('data/leveler/settings.json', "save", self.settings)

    async def _process_purchase(self, ctx):
        user = ctx.message.author
        server = ctx.message.server

        try:
            bank = self.bot.get_cog('Economy').bank
            if bank.account_exists(user) and self.settings["bg_price"] != 0:
                if not bank.can_spend(user, self.settings["bg_price"]):
                    await self.bot.say("**Insufficient funds. Backgrounds changes cost: ${}**".format(self.settings["bg_price"]))
                    return False
                else:
                    await self.bot.say('**{}, you are about to buy a background for `{}`. Confirm by typing `yes`.**'.format(self._is_mention(user), self.settings["bg_price"]))
                    answer = await self.bot.wait_for_message(timeout=15, author=user)
                    if answer is None:
                        await self.bot.say('**Purchase canceled.**')
                        return False
                    elif "yes" not in answer.content.lower():
                        await self.bot.say('**Background not purchased.**')
                        return False
                    else:
                        new_balance = bank.get_balance(user) - self.settings["bg_price"]
                        bank.set_credits(user, new_balance)
                        return True
            else:
                if self.settings["bg_price"] == 0:
                    return True
                else:
                    await self.bot.say("**You don't have an account. Do {}bank register**".format(prefix))
                    return False
        except:
            if self.settings["bg_price"] == 0:
                return True
            else:
                await self.bot.say("**There was an error with economy cog. Fix to allow purchases or set price to $0. Currently ${}**".format(prefix, self.settings["bg_price"]))
                return False

    async def _give_chat_credit(self, user, server):
        try:
            bank = self.bot.get_cog('Economy').bank
            if bank.account_exists(user) and "msg_credits" in self.settings:
                bank.deposit_credits(user, self.settings["msg_credits"][server.id])
        except:
            pass

    @checks.is_owner()
    @lvladmin.command(no_pm=True)
    async def setprice(self, price:int):
        '''Set a price for background changes.'''
        if price < 0:
            await self.bot.say("**That is not a valid background price.**")
        else:
            self.settings["bg_price"] = price
            await self.bot.say("**Background price set to: `{}`!**".format(price))
            fileIO('data/leveler/settings.json', "save", self.settings)

    @checks.is_owner()
    @lvladmin.command(pass_context=True, no_pm=True)
    async def setlevel(self, ctx, user : discord.Member, level:int):
        '''Set a user's level. (What a cheater C:).'''
        org_user = ctx.message.author
        server = user.server
        channel = ctx.message.channel
        # creates user if doesn't exist
        await self._create_user(user, server)
        userinfo = db.users.find_one({'user_id':user.id})

        if server.id in self.settings["disabled_servers"]:
            await self.bot.say("Leveler commands for this server are disabled.")
            return

        if level < 0:
            await self.bot.say("**Please enter a positive number.**")
            return

        # get rid of old level exp
        old_server_exp = 0
        for i in range(userinfo["servers"][server.id]["level"]):
            old_server_exp += self._required_exp(i)
        userinfo["total_exp"] -= old_server_exp
        userinfo["total_exp"] -= userinfo["servers"][server.id]["current_exp"]

        # add in new exp
        total_exp = self._level_exp(level)
        userinfo["servers"][server.id]["current_exp"] = 0
        userinfo["servers"][server.id]["level"] = level
        userinfo["total_exp"] += total_exp

        db.users.update_one({'user_id':user.id}, {'$set':{
            "servers.{}.level".format(server.id): level,
            "servers.{}.current_exp".format(server.id): 0,
            "total_exp": userinfo["total_exp"]
            }})
        await self.bot.say("**{}'s Level has been set to `{}`.**".format(self._is_mention(user), level))
        await self._handle_levelup(user, userinfo, server, channel)

    @checks.is_owner()
    @lvladmin.command(no_pm=True)
    async def mention(self):
        '''Toggle mentions on messages.'''
        if "mention" not in self.settings.keys() or self.settings["mention"] == True:
            self.settings["mention"] = False
            await self.bot.say("**Mentions disabled.**")
        else:
            self.settings["mention"] = True
            await self.bot.say("**Mentions enabled.**")
        fileIO('data/leveler/settings.json', "save", self.settings)

    async def _valid_image_url(self, url):
        max_byte = 1000

        try:
            async with aiohttp.get(url) as r:
                image = await r.content.read()
            with open('data/leveler/test.png','wb') as f:
                f.write(image)
            image = Image.open('data/leveler/test.png').convert('RGBA')
            os.remove('data/leveler/test.png')
            return True
        except:
            return False

    @checks.admin_or_permissions(manage_server=True)
    @lvladmin.command(pass_context=True, no_pm=True)
    async def toggle(self, ctx):
        """Toggle most leveler commands on the current server."""
        server = ctx.message.server
        if server.id in self.settings["disabled_servers"]:
            self.settings["disabled_servers"] = list(filter(lambda a: a != server.id, self.settings["disabled_servers"]))
            await self.bot.say("**Leveler enabled on `{}`.**".format(server.name))
        else:
            self.settings["disabled_servers"].append(server.id)
            await self.bot.say("**Leveler disabled on `{}`.**".format(server.name))
        fileIO('data/leveler/settings.json', "save", self.settings)

    @checks.admin_or_permissions(manage_server=True)
    @lvladmin.command(pass_context=True, no_pm=True)
    async def textonly(self, ctx, all:str=None):
        """Toggle text-based messages on the server."""
        server = ctx.message.server
        user = ctx.message.author
        # deals with enabled array

        if "text_only" not in self.settings.keys():
            self.settings["text_only"] = []

        if all != None:
            if user.id == self.owner:
                if all == "disableall":
                    self.settings["text_only"] = []
                    await self.bot.say("**Text-only disabled for all servers.**")
                elif all == "enableall":
                    self.settings["lvl_msg"] = []
                    for server in self.bot.servers:
                        self.settings["text_only"].append(server.id)
                    await self.bot.say("**Text-only messages enabled for all servers.**")
            else:
                await self.bot.say("**No Permission.**")
        else:
            if server.id in self.settings["text_only"]:
                self.settings["text_only"].remove(server.id)
                await self.bot.say("**Text-only messages disabled for `{}`.**".format(server.name))
            else:
                self.settings["text_only"].append(server.id)
                await self.bot.say("**Text-only messages enabled for `{}`.**".format(server.name))
        fileIO('data/leveler/settings.json', "save", self.settings)

    @checks.admin_or_permissions(manage_server=True)
    @lvladmin.command(name="alerts", pass_context=True, no_pm=True)
    async def lvlalert(self, ctx, all:str=None):
        """Toggle level-up messages on the server."""
        server = ctx.message.server
        user = ctx.message.author

        # old version was boolean
        if not isinstance(self.settings["lvl_msg"], list):
            self.settings["lvl_msg"] = []

        if all != None:
            if user.id == self.owner:
                if all == "disableall":
                    self.settings["lvl_msg"] = []
                    await self.bot.say("**Level-up messages disabled for all servers.**")
                elif all == "enableall":
                    self.settings["lvl_msg"] = []
                    for server in self.bot.servers:
                        self.settings["lvl_msg"].append(server.id)
                    await self.bot.say("**Level-up messages enabled for all servers.**")
            else:
                await self.bot.say("**No Permission.**")
        else:
            if server.id in self.settings["lvl_msg"]:
                self.settings["lvl_msg"].remove(server.id)
                await self.bot.say("**Level-up alerts disabled for `{}`.**".format(server.name))
            else:
                self.settings["lvl_msg"].append(server.id)
                await self.bot.say("**Level-up alerts enabled for `{}`.**".format(server.name))
        fileIO('data/leveler/settings.json', "save", self.settings)

    @checks.admin_or_permissions(manage_server=True)
    @lvladmin.command(name="private", pass_context=True, no_pm=True)
    async def lvlprivate(self, ctx, all:str=None):
        """Toggles if lvl alert is a private message to the user."""
        server = ctx.message.server
        # deals with ENABLED array, not disabled

        if "private_lvl_msg" not in self.settings.keys():
            self.settings["private_lvl_msg"] = []

        if all != None:
            if user.id == self.owner:
                if all == "disableall":
                    self.settings["private_lvl_msg"] = []
                    await self.bot.say("**Private level-up messages disabled for all servers.**")
                elif all == "enableall":
                    self.settings["private_lvl_msg"] = []
                    for server in self.bot.servers:
                        self.settings["private_lvl_msg"].append(server.id)
                    await self.bot.say("**Private level-up messages enabled for all servers.**")
            else:
                await self.bot.say("**No Permission.**")
        else:
            if server.id in self.settings["private_lvl_msg"]:
                self.settings["private_lvl_msg"].remove(server.id)
                await self.bot.say("**Private level-up alerts disabled for `{}`.**".format(server.name))
            else:
                self.settings["private_lvl_msg"].append(server.id)
                await self.bot.say("**Private level-up alerts enabled for `{}`.**".format(server.name))

        fileIO('data/leveler/settings.json', "save", self.settings)

    @commands.group(pass_context=True)
    async def lvlbadge(self, ctx):
        """Badge Configuration Options"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            return

    @lvlbadge.command(name="available", pass_context=True, no_pm=True)
    async def available(self, ctx, global_badge:str = None):
        '''Get a list of available badges for server or 'global'.'''
        user = ctx.message.author
        server = ctx.message.server

        # get server stuff
        ids = [('global','Global',self.bot.user.avatar_url), (server.id, server.name, server.icon_url)]

        title_text = "**Available Badges**"
        index = 0
        for serverid, servername, icon_url in ids:
            em = discord.Embed(description='', colour=user.colour)
            em.set_author(name="{}".format(servername), icon_url = icon_url)
            msg = ""
            server_badge_info = db.badges.find_one({'server_id':serverid})
            if server_badge_info:
                server_badges = server_badge_info['badges']
                for badgename in server_badges:
                    badgeinfo = server_badges[badgename]
                    if badgeinfo['price'] == -1:
                        price = 'Non-purchasable'
                    elif badgeinfo['price'] == 0:
                        price = 'Free'
                    else:
                        price = badgeinfo['price']

                    msg += "**• {}** ({}) - {}\n".format(badgename, price, badgeinfo['description'])
            else:
                msg = "None"

            em.description = msg

            total_pages = 0
            for page in pagify(msg, ["\n"]):
                total_pages +=1

            counter = 1
            for page in pagify(msg, ["\n"]):
                if index == 0:
                    await self.bot.say(title_text, embed = em)
                else:
                    await self.bot.say(embed = em)
                index += 1

                em.set_footer(text = "Page {} of {}".format(counter, total_pages))
                counter += 1


    @lvlbadge.command(name="list", pass_context=True, no_pm=True)
    async def listuserbadges(self, ctx, user:discord.Member = None):
        '''Get the badges of a user.'''
        if user == None:
            user = ctx.message.author
        server = ctx.message.server
        await self._create_user(user, server)
        userinfo = db.users.find_one({'user_id':user.id})
        userinfo = self._badge_convert_dict(userinfo)

        # sort
        priority_badges = []
        for badgename in userinfo['badges'].keys():
            badge = userinfo['badges'][badgename]
            priority_num = badge["priority_num"]
            if priority_num != -1:
                priority_badges.append((badge, priority_num))
        sorted_badges = sorted(priority_badges, key=operator.itemgetter(1), reverse=True)

        badge_ranks = ""
        counter = 1
        for badge, priority_num in sorted_badges[:12]:
            badge_ranks += "**{}. {}** ({}) [{}] **—** {}\n".format(counter, badge['badge_name'], badge['server_name'], priority_num, badge['description'])
            counter += 1
        if not badge_ranks:
            badge_ranks = "None"

        em = discord.Embed(description='', colour=user.colour)

        total_pages = 0
        for page in pagify(badge_ranks, ["\n"]):
            total_pages +=1

        counter = 1
        for page in pagify(badge_ranks, ["\n"]):
            em.description = page
            em.set_author(name="Badges for {}".format(user.name), icon_url = user.avatar_url)
            em.set_footer(text = "Page {} of {}".format(counter, total_pages))
            await self.bot.say(embed = em)
            counter += 1

    @lvlbadge.command(name="get", pass_context=True, no_pm=True)
    async def get(self, ctx, name:str, global_badge:str = None):
        '''Get a badge from repository. optional = "-global"'''
        user = ctx.message.author
        server = ctx.message.server
        if global_badge == '-global':
            serverid = 'global'
        else:
            serverid = server.id
        await self._create_user(user, server)
        userinfo = db.users.find_one({'user_id':user.id})
        userinfo = self._badge_convert_dict(userinfo)
        server_badge_info = db.badges.find_one({'server_id':serverid})

        if server_badge_info:
            server_badges = server_badge_info['badges']
            if name in server_badges:

                if "{}_{}".format(name,str(serverid)) not in userinfo['badges'].keys():
                    badge_info = server_badges[name]
                    if badge_info['price'] == -1:
                        await self.bot.say('**That badge is not purchasable.**'.format(name))
                    elif badge_info['price'] == 0:
                        userinfo['badges']["{}_{}".format(name,str(serverid))] = server_badges[name]
                        db.users.update_one({'user_id':userinfo['user_id']}, {'$set':{
                            "badges":userinfo['badges'],
                            }})
                        await self.bot.say('**`{}` has been obtained.**'.format(name))
                    else:
                        # use the economy cog
                        bank = self.bot.get_cog('Economy').bank
                        await self.bot.say('**{}, you are about to buy the `{}` badge for `{}`. Confirm by typing "yes"**'.format(self._is_mention(user), name, badge_info['price']))
                        answer = await self.bot.wait_for_message(timeout=15, author=user)
                        if answer is None:
                            await self.bot.say('**Purchase canceled.**')
                            return
                        elif "yes" not in answer.content.lower():
                            await self.bot.say('**Badge not purchased.**')
                            return
                        else:
                            if bank.account_exists(user) and badge_info['price'] <= bank.get_balance(user):
                                bank.withdraw_credits(user, badge_info['price'])
                                userinfo['badges']["{}_{}".format(name,str(serverid))] = server_badges[name]
                                db.users.update_one({'user_id':userinfo['user_id']}, {'$set':{
                                    "badges":userinfo['badges'],
                                    }})
                                await self.bot.say('**You have bought the `{}` badge for `{}`.**'.format(name, badge_info['price']))
                            elif bank.account_exists(user) and bank.get_balance(user) < badge_info['price']:
                                await self.bot.say('**Not enough money! Need `{}` more.**'.format(badge_info['price'] - bank.get_balance(user)))
                            else:
                                await self.bot.say('**User does not exist in bank. Do {}bank register**'.format(prefix))
                else:
                    await self.bot.say('**{}, you already have this badge!**'.format(user.name))
            else:
                await self.bot.say('**The badge `{}` does not exist. (try `{}lvlbadge available`)**'.format(name, prefix[0]))
        else:
            await self.bot.say('**There are no badges to get! (try `{}lvlbadge get [name] -global`).**'.format(prefix[0]))

    @lvlbadge.command(name="set", pass_context=True, no_pm=True)
    async def set(self, ctx, name:str, priority_num:int):
        '''Set a badge to profile. -1(invis), 0(not on profile), max: 5000.'''
        user = ctx.message.author
        server = ctx.message.author
        await self._create_user(user, server)

        userinfo = db.users.find_one({'user_id':user.id})
        userinfo = self._badge_convert_dict(userinfo)

        if priority_num < -1 or priority_num > 5000:
            await self.bot.say("**Invalid priority number! -1-5000**")
            return

        for badge in userinfo['badges']:
            if userinfo['badges'][badge]['badge_name'] == name:
                userinfo['badges'][badge]['priority_num'] = priority_num
                db.users.update_one({'user_id':userinfo['user_id']}, {'$set':{
                    "badges":userinfo['badges'],
                    }})
                await self.bot.say("**The `{}` badge priority has been set to `{}`!**".format(userinfo['badges'][badge]['badge_name'], priority_num))
                break
        else:
            await self.bot.say("**You don't have that badge!**")

    def _badge_convert_dict(self, userinfo):
        if 'badges' not in userinfo or not isinstance(userinfo['badges'], dict):
            db.users.update_one({'user_id':userinfo['user_id']}, {'$set':{
                "badges":{},
                }})
        return db.users.find_one({'user_id':userinfo['user_id']})

    @checks.admin_or_permissions(manage_server=True)
    @lvlbadge.command(name="add", pass_context = True, no_pm=True)
    async def addbadge(self, ctx, name:str, bg_img:str, border_color:str, price:int, *, description:str):
        """Add a badge. name = "Use Quotes", Colors = #hex. bg_img = url, price = -1(non-purchasable), 0,..."""

        user = ctx.message.author
        server = ctx.message.server

        # check members
        required_members = 35
        members = 0
        for member in server.members:
            if not member.bot:
                members += 1

        if user.id == self.owner:
            pass
        elif members < required_members:
            await self.bot.say("**You may only add badges in servers with {}+ non-bot members**".format(required_members))
            return

        if '-global' in description and user.id == self.owner:
            description = description.replace('-global', '')
            serverid = 'global'
            servername = 'global'
        else:
            serverid = server.id
            servername = server.name

        if '.' in name:
            await self.bot.say("**Name cannot contain `.`**")
            return

        if not await self._valid_image_url(bg_img):
            await self.bot.say("**Background is not valid. Enter hex or image url!**")
            return

        if not self._is_hex(border_color):
            await self.bot.say("**Border color is not valid!**")
            return

        if price < -1:
            await self.bot.say("**Price is not valid!**")
            return

        if len(description.split(" ")) > 40:
            await self.bot.say("**Description is too long! <=40**")
            return

        badges = db.badges.find_one({'server_id':serverid})
        if not badges:
            db.badges.insert_one({'server_id':serverid,
                'badges': {}})
            badges = db.badges.find_one({'server_id':serverid})

        new_badge = {
                "badge_name": name,
                "bg_img": bg_img,
                "price": price,
                "description": description,
                "border_color": border_color,
                "server_id": serverid,
                "server_name": servername,
                "priority_num": 0
            }

        if name not in badges['badges'].keys():
            # create the badge regardless
            badges['badges'][name] = new_badge
            db.badges.update_one({'server_id':serverid}, {'$set': {
                'badges': badges['badges']
                }})
            await self.bot.say("**`{}` Badge added in `{}` server.**".format(name, servername))
        else:
            # update badge in the server
            badges['badges'][name] = new_badge
            db.badges.update_one({'server_id':serverid}, {'$set': {
                'badges': badges['badges']
                }})

            # go though all users and update the badge. Doing it this way because dynamic does more accesses when doing profile
            for user in db.users.find({}):
                try:
                    user = self._badge_convert_dict(user)
                    userbadges = user['badges']
                    badge_name = "{}_{}".format(name, serverid)
                    if badge_name in userbadges.keys():
                        user_priority_num = userbadges[badge_name]['priority_num']
                        new_badge['priority_num'] = user_priority_num # maintain old priority number set by user
                        userbadges[badge_name] = new_badge
                        db.users.update_one({'user_id':user['user_id']}, {'$set': {
                            'badges': userbadges
                            }})
                except:
                    pass
            await self.bot.say("**The `{}` badge has been updated**".format(name))

    @checks.is_owner()
    @lvlbadge.command(no_pm=True)
    async def type(self, name:str):
        """circles or bars."""
        valid_types = ["circles", "bars"]
        if name.lower() not in valid_types:
            await self.bot.say("**That is not a valid badge type!**")
            return

        self.settings["badge_type"] = name.lower()
        await self.bot.say("**Badge type set to `{}`**".format(name.lower()))
        fileIO('data/leveler/settings.json', "save", self.settings)

    def _is_hex(self, color:str):
        if color != None and len(color) != 4 and len(color) != 7:
            return False

        reg_ex = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
        return re.search(reg_ex, str(color))

    @checks.admin_or_permissions(manage_server=True)
    @lvlbadge.command(name="delete", pass_context=True, no_pm=True)
    async def delbadge(self, ctx, *, name:str):
        """Delete a badge and remove from all users."""
        user = ctx.message.author
        channel = ctx.message.channel
        server = user.server

        if '-global' in name and user.id == self.owner:
            name = name.replace(' -global', '')
            serverid = 'global'
        else:
            serverid = server.id

        # creates user if doesn't exist
        await self._create_user(user, server)
        userinfo = db.users.find_one({'user_id':user.id})
        userinfo = self._badge_convert_dict(userinfo)

        if server.id in self.settings["disabled_servers"]:
            await self.bot.say("Leveler commands for this server are disabled.")
            return

        serverbadges = db.badges.find_one({'server_id':serverid})
        if name in serverbadges['badges'].keys():
            del serverbadges['badges'][name]
            db.badges.update_one({'server_id':serverbadges['server_id']}, {'$set':{
                "badges":serverbadges["badges"],
                }})
            # remove the badge if there
            for user_info_temp in db.users.find({}):
                try:
                    user_info_temp = self._badge_convert_dict(user_info_temp)

                    badge_name = "{}_{}".format(name, serverid)
                    if badge_name in user_info_temp["badges"].keys():
                        del user_info_temp["badges"][badge_name]
                        db.users.update_one({'user_id':user_info_temp['user_id']}, {'$set':{
                            "badges":user_info_temp["badges"],
                            }})
                except:
                    pass

            await self.bot.say("**The `{}` badge has been removed.**".format(name))
        else:
            await self.bot.say("**That badge does not exist.**")

    @checks.admin_or_permissions(manage_server=True)
    @lvlbadge.command(pass_context = True, no_pm=True)
    async def give(self, ctx, user : discord.Member, name: str):
        """Give a user a badge with a certain name"""
        org_user = ctx.message.author
        server = org_user.server
        # creates user if doesn't exist
        await self._create_user(user, server)
        userinfo = db.users.find_one({'user_id':user.id})
        userinfo = self._badge_convert_dict(userinfo)

        if server.id in self.settings["disabled_servers"]:
            await self.bot.say("Leveler commands for this server are disabled.")
            return

        serverbadges = db.badges.find_one({'server_id':server.id})
        badges = serverbadges['badges']
        badge_name = "{}_{}".format(name, server.id)

        if name not in badges:
            await self.bot.say("**That badge doesn't exist in this server!**")
            return
        elif badge_name in badges.keys():
            await self.bot.say("**{} already has that badge!**".format(self._is_mention(user)))
            return
        else:
            userinfo["badges"][badge_name] = badges[name]
            db.users.update_one({'user_id':user.id}, {'$set':{"badges": userinfo["badges"]}})
            await self.bot.say("**{} has just given `{}` the `{}` badge!**".format(self._is_mention(org_user), self._is_mention(user), name))

    @checks.admin_or_permissions(manage_server=True)
    @lvlbadge.command(pass_context = True, no_pm=True)
    async def take(self, ctx, user : discord.Member, name: str):
        """Take a user's badge."""
        org_user = ctx.message.author
        server = org_user.server
        # creates user if doesn't exist
        await self._create_user(user, server)
        userinfo = db.users.find_one({'user_id':user.id})
        userinfo = self._badge_convert_dict(userinfo)

        if server.id in self.settings["disabled_servers"]:
            await self.bot.say("Leveler commands for this server are disabled.")
            return

        serverbadges = db.badges.find_one({'server_id':server.id})
        badges = serverbadges['badges']
        badge_name = "{}_{}".format(name, server.id)

        if name not in badges:
            await self.bot.say("**That badge doesn't exist in this server!**")
        elif badge_name not in userinfo["badges"]:
            await self.bot.say("**{} does not have that badge!**".format(self._is_mention(user)))
        else:
            if userinfo['badges'][badge_name]['price'] == -1:
                del userinfo["badges"][badge_name]
                db.users.update_one({'user_id':user.id}, {'$set':{"badges": userinfo["badges"]}})
                await self.bot.say("**{} has taken the `{}` badge from {}! :upside_down:**".format(self._is_mention(org_user), name, self._is_mention(user)))
            else:
                await self.bot.say("**You can't take away purchasable badges!**")

    @lvladmin.group(name = "bg", pass_context=True)
    async def lvladminbg(self, ctx):
        """Admin Background Configuration"""
        if ctx.invoked_subcommand is None or \
                isinstance(ctx.invoked_subcommand, commands.Group):
            await send_cmd_help(ctx)
            return

    @checks.is_owner()
    @lvladminbg.command(no_pm=True)
    async def addprofilebg(self, name:str, url:str):
        """Add a profile background. Proportions: (290px x 290px)"""
        if name in self.backgrounds["profile"].keys():
            await self.bot.say("**That profile background name already exists!**")
        elif not await self._valid_image_url(url):
            await self.bot.say("**That is not a valid image url!**")
        else:
            self.backgrounds["profile"][name] = url
            fileIO('data/leveler/backgrounds.json', "save", self.backgrounds)
            await self.bot.say("**New profile background(`{}`) added.**".format(name))

    @checks.is_owner()
    @lvladminbg.command(no_pm=True)
    async def addrankbg(self, name:str, url:str):
        """Add a rank background. Proportions: (360px x 100px)"""
        if name in self.backgrounds["rank"].keys():
            await self.bot.say("**That rank background name already exists!**")
        elif not await self._valid_image_url(url):
            await self.bot.say("**That is not a valid image url!**")
        else:
            self.backgrounds["rank"][name] = url
            fileIO('data/leveler/backgrounds.json', "save", self.backgrounds)
            await self.bot.say("**New rank background(`{}`) added.**".format(name))

    @checks.is_owner()
    @lvladminbg.command(no_pm=True)
    async def addlevelbg(self, name:str, url:str):
        '''Add a level-up background. Proportions: (85px x 105px)'''
        if name in self.backgrounds["levelup"].keys():
            await self.bot.say("**That level-up background name already exists!**")
        elif not await self._valid_image_url(url):
            await self.bot.say("**That is not a valid image url!**")
        else:
            self.backgrounds["levelup"][name] = url
            fileIO('data/leveler/backgrounds.json', "save", self.backgrounds)
            await self.bot.say("**New level-up background(`{}`) added.**".format(name))

    @checks.is_owner()
    @lvladminbg.command(no_pm=True)
    async def delprofilebg(self, name:str):
        '''Delete a profile background.'''
        if name in self.backgrounds["profile"].keys():
            del self.backgrounds["profile"][name]
            fileIO('data/leveler/backgrounds.json', "save", self.backgrounds)
            await self.bot.say("**The profile background(`{}`) has been deleted.**".format(name))
        else:
            await self.bot.say("**That profile background name doesn't exist.**")

    @checks.is_owner()
    @lvladminbg.command(no_pm=True)
    async def delrankbg(self, name:str):
        '''Delete a rank background.'''
        if name in self.backgrounds["rank"].keys():
            del self.backgrounds["rank"][name]
            fileIO('data/leveler/backgrounds.json', "save", self.backgrounds)
            await self.bot.say("**The rank background(`{}`) has been deleted.**".format(name))
        else:
            await self.bot.say("**That rank background name doesn't exist.**")

    @checks.is_owner()
    @lvladminbg.command(no_pm=True)
    async def dellevelbg(self, name:str):
        '''Delete a level background.'''
        if name in self.backgrounds["levelup"].keys():
            del self.backgrounds["levelup"][name]
            fileIO('data/leveler/backgrounds.json', "save", self.backgrounds)
            await self.bot.say("**The level-up background(`{}`) has been deleted.**".format(name))
        else:
            await self.bot.say("**That level-up background name doesn't exist.**")

    @lvlset.command(name="listbgs", pass_context=True, no_pm=True)
    async def listbgs(self, ctx, type:str = None):
        '''Gives a list of backgrounds. [p]lvlset listbgs [profile|rank|levelup]'''
        server = ctx.message.server
        user = ctx.message.author
        max_all = 18

        if server.id in self.settings["disabled_servers"]:
            await self.bot.say("**Leveler commands for this server are disabled!**")
            return

        em = discord.Embed(description='', colour=user.colour)
        if not type:
            em.set_author(name="All Backgrounds for {}".format(self.bot.user.name), icon_url = self.bot.user.avatar_url)

            for category in self.backgrounds.keys():
                bg_url = []
                for background_name in sorted(self.backgrounds[category].keys()):
                    bg_url.append("[{}]({})".format(background_name, self.backgrounds[category][background_name]))
                max_bg = min(max_all, len(bg_url))
                bgs = ", ".join(bg_url[0:max_bg])
                if len(bg_url) >= max_all:
                    bgs += "..."
                em.add_field(name = category.upper(), value = bgs)
            await self.bot.say(embed = em)
        else:
            if type.lower() == "profile":
                em.set_author(name="Profile Backgrounds for {}".format(self.bot.user.name), icon_url = self.bot.user.avatar_url)
                bg_key = "profile"
            elif type.lower() == "rank":
                em.set_author(name="Rank Backgrounds for {}".format(self.bot.user.name), icon_url = self.bot.user.avatar_url)
                bg_key = "rank"
            elif type.lower() == "levelup":
                em.set_author(name="Level Up Backgrounds for {}".format(self.bot.user.name), icon_url = self.bot.user.avatar_url)
                bg_key = "levelup"
            else:
                bg_key = None

            if bg_key:
                bg_url = []
                for background_name in sorted(self.backgrounds[bg_key].keys()):
                    bg_url.append("[{}]({})".format(background_name, self.backgrounds[bg_key][background_name]))
                bgs = ", ".join(bg_url)

                total_pages = 0
                for page in pagify(bgs, [" "]):
                    total_pages +=1

                counter = 1
                for page in pagify(bgs, [" "]):
                    em.description = page
                    em.set_footer(text = "Page {} of {}".format(counter, total_pages))
                    await self.bot.say(embed = em)
                    counter += 1
            else:
                await self.bot.say("**Invalid Background Type. (profile, rank, levelup)**")

    async def draw_profile(self, user, server):
        name_fnt = ImageFont.truetype(font_bold_file, 22)
        header_u_fnt = ImageFont.truetype(font_unicode_file, 18)
        title_fnt = ImageFont.truetype(font_file, 18)
        sub_header_fnt = ImageFont.truetype(font_bold_file, 14)
        badge_fnt = ImageFont.truetype(font_bold_file, 10)
        exp_fnt = ImageFont.truetype(font_bold_file, 13)
        large_fnt = ImageFont.truetype(font_bold_file, 33)
        level_label_fnt = ImageFont.truetype(font_bold_file, 22)
        general_info_fnt = ImageFont.truetype(font_bold_file, 15)
        general_info_u_fnt = ImageFont.truetype(font_unicode_file, 12)
        rep_fnt = ImageFont.truetype(font_bold_file, 26)
        text_fnt = ImageFont.truetype(font_bold_file, 12)
        text_u_fnt = ImageFont.truetype(font_unicode_file, 8)
        credit_fnt = ImageFont.truetype(font_bold_file, 10)

        def _write_unicode(text, init_x, y, font, unicode_font, fill):
            write_pos = init_x

            for char in text:
                if char.isalnum() or char in string.punctuation or char in string.whitespace:
                    draw.text((write_pos, y), char, font=font, fill=fill)
                    write_pos += font.getsize(char)[0]
                else:
                    draw.text((write_pos, y), u"{}".format(char), font=unicode_font, fill=fill)
                    write_pos += unicode_font.getsize(char)[0]

        # get urls
        userinfo = db.users.find_one({'user_id':user.id})
        self._badge_convert_dict(userinfo)
        userinfo = db.users.find_one({'user_id':user.id}) ##############################################
        bg_url = userinfo["profile_background"]
        profile_url = user.avatar_url

        # create image objects
        bg_image = Image
        profile_image = Image

        async with aiohttp.get(bg_url) as r:
            image = await r.content.read()
        with open('data/leveler/temp/{}_temp_profile_bg.png'.format(user.id),'wb') as f:
            f.write(image)
        try:
            async with aiohttp.get(profile_url) as r:
                image = await r.content.read()
        except:
            async with aiohttp.get(default_avatar_url) as r:
                image = await r.content.read()
        with open('data/leveler/temp/{}_temp_profile_profile.png'.format(user.id),'wb') as f:
            f.write(image)

        bg_image = Image.open('data/leveler/temp/{}_temp_profile_bg.png'.format(user.id)).convert('RGBA')
        profile_image = Image.open('data/leveler/temp/{}_temp_profile_profile.png'.format(user.id)).convert('RGBA')

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
        vert_pos = 110
        left_pos = 70
        right_pos = 285
        title_height = 22
        gap = 3

        # determines rep section color
        if "rep_color" not in userinfo.keys() or not userinfo["rep_color"]:
            rep_fill = (92,130,203,230)
        else:
            rep_fill = tuple(userinfo["rep_color"])
        # determines badge section color, should be behind the titlebar
        if "badge_col_color" not in userinfo.keys() or not userinfo["badge_col_color"]:
            badge_fill = (128,151,165,230)
        else:
            badge_fill = tuple(userinfo["badge_col_color"])

        if "profile_info_color" in userinfo.keys():
            info_color = tuple(userinfo["profile_info_color"])
        else:
            info_color = (30, 30 ,30, 220)

        draw.rectangle([(left_pos - 20, vert_pos + title_height), (right_pos, 156)], fill=info_color) # title box
        draw.rectangle([(100,159), (285, 212)], fill=info_color) # general content
        draw.rectangle([(100,215), (285, 285)], fill=info_color) # info content

        # stick in credits if needed
        if bg_url in bg_credits.keys():
            credit_text = "  ".join("Background by {}".format(bg_credits[bg_url]))
            credit_init = 290 - credit_fnt.getsize(credit_text)[0]
            draw.text((credit_init, 0), credit_text,  font=credit_fnt, fill=(0,0,0,100))
        draw.rectangle([(5, vert_pos), (right_pos, vert_pos + title_height)], fill=(230,230,230,230)) # name box in front

        # draw level circle
        multiplier = 8
        lvl_circle_dia = 104
        circle_left = 1
        circle_top = 42
        raw_length = lvl_circle_dia * multiplier

        # create mask
        mask = Image.new('L', (raw_length, raw_length), 0)
        draw_thumb = ImageDraw.Draw(mask)
        draw_thumb.ellipse((0, 0) + (raw_length, raw_length), fill = 255, outline = 0)

        # drawing level bar calculate angle
        start_angle = -90 # from top instead of 3oclock
        angle = int(360 * (userinfo["servers"][server.id]["current_exp"]/self._required_exp(userinfo["servers"][server.id]["level"]))) + start_angle

        # level outline
        lvl_circle = Image.new("RGBA", (raw_length, raw_length))
        draw_lvl_circle = ImageDraw.Draw(lvl_circle)
        draw_lvl_circle.ellipse([0, 0, raw_length, raw_length], fill=(badge_fill[0], badge_fill[1], badge_fill[2], 180), outline = (255, 255, 255, 250))
        # determines exp bar color
        if "profile_exp_color" not in userinfo.keys() or not userinfo["profile_exp_color"]:
            exp_fill = (255, 255, 255, 230)
        else:
            exp_fill = tuple(userinfo["profile_exp_color"])
        draw_lvl_circle.pieslice([0, 0, raw_length, raw_length], start_angle, angle, fill=exp_fill, outline = (255, 255, 255, 255))
        # put on level bar circle
        lvl_circle = lvl_circle.resize((lvl_circle_dia, lvl_circle_dia), Image.ANTIALIAS)
        lvl_bar_mask = mask.resize((lvl_circle_dia, lvl_circle_dia), Image.ANTIALIAS)
        process.paste(lvl_circle, (circle_left, circle_top), lvl_bar_mask)

        # draws boxes
        draw.rectangle([(5,133), (100, 285)], fill= badge_fill) # badges
        draw.rectangle([(10,138), (95, 168)], fill = rep_fill) # reps

        total_gap = 10
        border = int(total_gap/2)
        profile_size = lvl_circle_dia - total_gap
        raw_length = profile_size * multiplier
        # put in profile picture
        output = ImageOps.fit(profile_image, (raw_length, raw_length), centering=(0.5, 0.5))
        output = output.resize((profile_size, profile_size), Image.ANTIALIAS)
        mask = mask.resize((profile_size, profile_size), Image.ANTIALIAS)
        profile_image = profile_image.resize((profile_size, profile_size), Image.ANTIALIAS)
        process.paste(profile_image, (circle_left + border, circle_top + border), mask)

        # write label text
        white_color = (240,240,240,255)
        light_color = (160,160,160,255)

        head_align = 105
        _write_unicode(self._truncate_text(self._name(user, 22), 22), head_align, vert_pos + 3, level_label_fnt, header_u_fnt, (110,110,110,255)) # NAME
        _write_unicode(userinfo["title"], head_align, 136, level_label_fnt, header_u_fnt, white_color)

        # draw level box
        level_right = 290
        level_left = level_right - 78
        draw.rectangle([(level_left, 0), (level_right, 21)], fill=(badge_fill[0],badge_fill[1],badge_fill[2],160)) # box
        lvl_text = "LEVEL {}".format(userinfo["servers"][server.id]["level"])
        if badge_fill == (128,151,165,230):
            lvl_color = white_color
        else:
            lvl_color = self._contrast(badge_fill, rep_fill, exp_fill)
        draw.text((self._center(level_left+2, level_right, lvl_text, level_label_fnt), 2), lvl_text,  font=level_label_fnt, fill=(lvl_color[0],lvl_color[1],lvl_color[2],255)) # Level #

        rep_text = "{} REP".format(userinfo["rep"])
        draw.text((self._center(7, 100, rep_text, rep_fnt), 144), rep_text, font=rep_fnt, fill=white_color)

        exp_text = "{}/{}".format(userinfo["servers"][server.id]["current_exp"],self._required_exp(userinfo["servers"][server.id]["level"])) # Exp
        exp_color = exp_fill
        draw.text((105, 99), exp_text,  font=exp_fnt, fill=(exp_color[0], exp_color[1], exp_color[2], 255)) # Exp Text

        # determine info text color
        dark_text = (35, 35, 35, 230)
        info_text_color = self._contrast(info_color, light_color, dark_text)

        lvl_left = 100
        label_align = 105
        _write_unicode(u"Rank:", label_align, 165, general_info_fnt, general_info_u_fnt, info_text_color)
        draw.text((label_align, 180), "Exp:",  font=general_info_fnt, fill=info_text_color) # Exp
        draw.text((label_align, 195), "Credits:",  font=general_info_fnt, fill=info_text_color) # Credits

        # local stats
        num_local_align = 172
        local_symbol = u"\U0001F3E0 "
        if "linux" in platform.system().lower():
            local_symbol = u"\U0001F3E0 "
        else:
            local_symbol = "S "

        s_rank_txt = local_symbol + self._truncate_text("#{}".format(await self._find_server_rank(user, server)), 8)
        _write_unicode(s_rank_txt, num_local_align - general_info_u_fnt.getsize(local_symbol)[0], 165, general_info_fnt, general_info_u_fnt, info_text_color) # Rank

        s_exp_txt = self._truncate_text("{}".format(await self._find_server_exp(user, server)), 8)
        _write_unicode(s_exp_txt, num_local_align, 180, general_info_fnt, general_info_u_fnt, info_text_color)  # Exp
        try:
            bank = self.bot.get_cog('Economy').bank
            if bank.account_exists(user):
                credits = bank.get_balance(user)
            else:
                credits = 0
        except:
            credits = 0
        credit_txt = "${}".format(credits)
        draw.text((num_local_align, 195), self._truncate_text(credit_txt, 18),  font=general_info_fnt, fill=info_text_color) # Credits

        # global stats
        num_align = 230
        if "linux" in platform.system().lower():
            global_symbol = u"\U0001F30E "
            fine_adjust = 1
        else:
            global_symbol = "G "
            fine_adjust = 0

        rank_txt = global_symbol + self._truncate_text("#{}".format(await self._find_global_rank(user, server)), 8)
        exp_txt = self._truncate_text("{}".format(userinfo["total_exp"]), 8)
        _write_unicode(rank_txt, num_align - general_info_u_fnt.getsize(global_symbol)[0] + fine_adjust, 165, general_info_fnt, general_info_u_fnt, info_text_color) # Rank
        _write_unicode(exp_txt, num_align, 180, general_info_fnt, general_info_u_fnt, info_text_color)  # Exp

        draw.text((105, 220), "Info Box",  font=sub_header_fnt, fill=white_color) # Info Box
        margin = 105
        offset = 238
        for line in textwrap.wrap(userinfo["info"], width=42):
            # draw.text((margin, offset), line, font=text_fnt, fill=(70,70,70,255))
            _write_unicode(line, margin, offset, text_fnt, text_u_fnt, info_text_color)
            offset += text_fnt.getsize(line)[1] + 2

        # sort badges
        priority_badges = []

        for badgename in userinfo['badges'].keys():
            badge = userinfo['badges'][badgename]
            priority_num = badge["priority_num"]
            if priority_num != 0 and priority_num != -1:
                priority_badges.append((badge, priority_num))
        sorted_badges = sorted(priority_badges, key=operator.itemgetter(1), reverse=True)

        # TODO: simplify this. it shouldn't be this complicated... sacrifices conciseness for customizability
        if "badge_type" not in self.settings.keys() or self.settings["badge_type"] == "circles":
            # circles require antialiasing
            vert_pos = 171
            right_shift = 0
            left = 9 + right_shift
            right = 52 + right_shift
            size = 27
            total_gap = 4 # /2
            hor_gap = 3
            vert_gap = 2
            border_width = int(total_gap/2)
            mult = [
                (0,0), (1,0), (2,0),
                (0,1), (1,1), (2,1),
                (0,2), (1,2), (2,2),
                (0,3), (1,3), (2,3),
                ]
            i = 0
            for pair in sorted_badges[:12]:
                try:
                    coord = (left + int(mult[i][0])*int(hor_gap+size), vert_pos + int(mult[i][1])*int(vert_gap + size))
                    badge = pair[0]
                    bg_color = badge["bg_img"]
                    border_color = badge["border_color"]
                    multiplier = 6 # for antialiasing
                    raw_length = size * multiplier

                    # draw mask circle
                    mask = Image.new('L', (raw_length, raw_length), 0)
                    draw_thumb = ImageDraw.Draw(mask)
                    draw_thumb.ellipse((0, 0) + (raw_length, raw_length), fill = 255, outline = 0)

                    # determine image or color for badge bg
                    if await self._valid_image_url(bg_color):
                        # get image
                        async with aiohttp.get(bg_color) as r:
                            image = await r.content.read()
                        with open('data/leveler/temp/{}_temp_badge.png'.format(user.id),'wb') as f:
                            f.write(image)
                        badge_image = Image.open('data/leveler/temp/{}_temp_badge.png'.format(user.id)).convert('RGBA')
                        badge_image = badge_image.resize((raw_length, raw_length), Image.ANTIALIAS)

                        # structured like this because if border = 0, still leaves outline.
                        if border_color:
                            square = Image.new('RGBA', (raw_length, raw_length), border_color)
                            # put border on ellipse/circle
                            output = ImageOps.fit(square, (raw_length, raw_length), centering=(0.5, 0.5))
                            output = output.resize((size, size), Image.ANTIALIAS)
                            outer_mask = mask.resize((size, size), Image.ANTIALIAS)
                            process.paste(output, coord, outer_mask)

                            # put on ellipse/circle
                            output = ImageOps.fit(badge_image, (raw_length, raw_length), centering=(0.5, 0.5))
                            output = output.resize((size - total_gap, size - total_gap), Image.ANTIALIAS)
                            inner_mask = mask.resize((size - total_gap, size - total_gap), Image.ANTIALIAS)
                            process.paste(output, (coord[0] + border_width, coord[1] + border_width), inner_mask)
                        else:
                            # put on ellipse/circle
                            output = ImageOps.fit(badge_image, (raw_length, raw_length), centering=(0.5, 0.5))
                            output = output.resize((size, size), Image.ANTIALIAS)
                            outer_mask = mask.resize((size, size), Image.ANTIALIAS)
                            process.paste(output, coord, outer_mask)
                except:
                    pass
                # attempt to remove badge image
                try:
                    os.remove('data/leveler/temp/{}_temp_badge.png'.format(user.id))
                except:
                    pass
                i += 1
        elif self.settings["badge_type"] == "tags" or self.settings["badge_type"] == "bars":
            vert_pos = 187
            i = 0
            for pair in sorted_badges[:5]:
                badge = pair[0]
                print(badge)
                bg_color = badge["bg_img"]
                border_color = badge["border_color"]
                left_pos = 10
                right_pos = 95
                total_gap = 4
                border_width = int(total_gap/2)
                bar_size = (85, 15)

                # determine image or color for badge bg
                if await self._valid_image_url(bg_color):
                    async with aiohttp.get(bg_color) as r:
                        image = await r.content.read()
                    with open('data/leveler/temp/{}_temp_badge.png'.format(user.id),'wb') as f:
                        f.write(image)
                    badge_image = Image.open('data/leveler/temp/{}_temp_badge.png'.format(user.id)).convert('RGBA')

                    if border_color != None:
                        draw.rectangle([(left_pos, vert_pos + i*17), (right_pos, vert_pos + 15 + i*17)], fill = border_color, outline = border_color) # border
                        badge_image = badge_image.resize((bar_size[0] - total_gap + 1, bar_size[1] - total_gap + 1), Image.ANTIALIAS)
                        process.paste(badge_image, (left_pos + border_width, vert_pos + border_width + i*17))
                    else:
                        badge_image = badge_image.resize(bar_size, Image.ANTIALIAS)
                        process.paste(badge_image, (left_pos,vert_pos + i*17))
                    try:
                        os.remove('data/leveler/temp/{}_temp_badge.png'.format(user.id))
                    except:
                        pass

                vert_pos += 3 # spacing
                i += 1

        result = Image.alpha_composite(result, process)
        result.save('data/leveler/temp/{}_profile.png'.format(user.id),'PNG', quality=100)

        # remove images
        try:
            os.remove('data/leveler/temp/{}_temp_profile_bg.png'.format(user.id))
        except:
            pass
        try:
            os.remove('data/leveler/temp/{}_temp_profile_profile.png'.format(user.id))
        except:
            pass

    # returns color that contrasts better in background
    def _contrast(self, bg_color, color1, color2):
        color1_ratio = self._contrast_ratio(bg_color, color1)
        color2_ratio = self._contrast_ratio(bg_color, color2)
        if color1_ratio >= color2_ratio:
            return color1
        else:
            return color2

    def _luminance(self, color):
        # convert to greyscale
        luminance = float((0.2126*color[0]) + (0.7152*color[1]) + (0.0722*color[2]))
        return luminance

    def _contrast_ratio(self, bgcolor, foreground):
        f_lum = float(self._luminance(foreground)+0.05)
        bg_lum = float(self._luminance(bgcolor)+0.05)

        if bg_lum > f_lum:
            return bg_lum/f_lum
        else:
            return f_lum/bg_lum

    # returns a string with possibly a nickname
    def _name(self, user, max_length):
        if user.name == user.display_name:
            return user.name
        else:
            return "{} ({})".format(user.name, self._truncate_text(user.display_name, max_length - len(user.name) - 3), max_length)

    async def draw_rank(self, user, server):

        # fonts
        name_fnt = ImageFont.truetype(font_bold_file, 22)
        header_u_fnt = ImageFont.truetype(font_unicode_file, 18)
        sub_header_fnt = ImageFont.truetype(font_bold_file, 14)
        badge_fnt = ImageFont.truetype(font_bold_file, 12)
        large_fnt = ImageFont.truetype(font_bold_file, 33)
        level_label_fnt = ImageFont.truetype(font_bold_file, 22)
        general_info_fnt = ImageFont.truetype(font_bold_file, 15)
        general_info_u_fnt = ImageFont.truetype(font_unicode_file, 11)
        credit_fnt = ImageFont.truetype(font_bold_file, 10)

        def _write_unicode(text, init_x, y, font, unicode_font, fill):
            write_pos = init_x

            for char in text:
                if char.isalnum() or char in string.punctuation or char in string.whitespace:
                    draw.text((write_pos, y), char, font=font, fill=fill)
                    write_pos += font.getsize(char)[0]
                else:
                    draw.text((write_pos, y), u"{}".format(char), font=unicode_font, fill=fill)
                    write_pos += unicode_font.getsize(char)[0]

        userinfo = db.users.find_one({'user_id':user.id})
        # get urls
        bg_url = userinfo["rank_background"]
        profile_url = user.avatar_url
        server_icon_url = server.icon_url

        # create image objects
        bg_image = Image
        profile_image = Image

        async with aiohttp.get(bg_url) as r:
            image = await r.content.read()
        with open('data/leveler/temp/{}_temp_rank_bg.png'.format(user.id),'wb') as f:
            f.write(image)
        try:
            async with aiohttp.get(profile_url) as r:
                image = await r.content.read()
        except:
            async with aiohttp.get(default_avatar_url) as r:
                image = await r.content.read()
        with open('data/leveler/temp/{}_temp_rank_profile.png'.format(user.id),'wb') as f:
            f.write(image)
        try:
            async with aiohttp.get(server_icon_url) as r:
                image = await r.content.read()
        except:
            async with aiohttp.get(default_avatar_url) as r:
                image = await r.content.read()
        with open('data/leveler/temp/{}_temp_server_icon.png'.format(user.id),'wb') as f:
            f.write(image)

        bg_image = Image.open('data/leveler/temp/{}_temp_rank_bg.png'.format(user.id)).convert('RGBA')
        profile_image = Image.open('data/leveler/temp/{}_temp_rank_profile.png'.format(user.id)).convert('RGBA')
        server_image = Image.open('data/leveler/temp/{}_temp_server_icon.png'.format(user.id)).convert('RGBA')

        # set canvas
        width = 360
        height = 100
        bg_color = (255,255,255, 0)
        result = Image.new('RGBA', (width, height), bg_color)
        process = Image.new('RGBA', (width, height), bg_color)

        # puts in background
        bg_image = bg_image.resize((width, height), Image.ANTIALIAS)
        bg_image = bg_image.crop((0,0, width, height))
        result.paste(bg_image, (0,0))

        # draw
        draw = ImageDraw.Draw(process)

        # draw transparent overlay
        vert_pos = 5
        left_pos = 70
        right_pos = width - vert_pos
        title_height = 22
        gap = 3

        draw.rectangle([(left_pos - 20,vert_pos), (right_pos, vert_pos + title_height)], fill=(230,230,230,230)) # title box
        content_top = vert_pos + title_height + gap
        content_bottom = 100 - vert_pos

        if "rank_info_color" in userinfo.keys():
            info_color = tuple(userinfo["rank_info_color"])
            info_color = (info_color[0], info_color[1], info_color[2], 160) # increase transparency
        else:
            info_color = (30, 30 ,30, 160)
        draw.rectangle([(left_pos - 20, content_top), (right_pos, content_bottom)], fill=info_color, outline=(180, 180, 180, 180)) # content box

        # stick in credits if needed
        if bg_url in bg_credits.keys():
            credit_text = " ".join("{}".format(bg_credits[bg_url]))
            draw.text((2, 92), credit_text,  font=credit_fnt, fill=(0,0,0,190))

        # draw level circle
        multiplier = 6
        lvl_circle_dia = 94
        circle_left = 15
        circle_top = int((height- lvl_circle_dia)/2)
        raw_length = lvl_circle_dia * multiplier

        # create mask
        mask = Image.new('L', (raw_length, raw_length), 0)
        draw_thumb = ImageDraw.Draw(mask)
        draw_thumb.ellipse((0, 0) + (raw_length, raw_length), fill = 255, outline = 0)

        # drawing level bar calculate angle
        start_angle = -90 # from top instead of 3oclock
        angle = int(360 * (userinfo["servers"][server.id]["current_exp"]/self._required_exp(userinfo["servers"][server.id]["level"]))) + start_angle

        lvl_circle = Image.new("RGBA", (raw_length, raw_length))
        draw_lvl_circle = ImageDraw.Draw(lvl_circle)
        draw_lvl_circle.ellipse([0, 0, raw_length, raw_length], fill=(180, 180, 180, 180), outline = (255, 255, 255, 220))
        # determines exp bar color
        if "rank_exp_color" not in userinfo.keys() or not userinfo["rank_exp_color"]:
            exp_fill = (255, 255, 255, 230)
        else:
            exp_fill = tuple(userinfo["rank_exp_color"])
        draw_lvl_circle.pieslice([0, 0, raw_length, raw_length], start_angle, angle, fill=exp_fill, outline = (255, 255, 255, 230))
        # put on level bar circle
        lvl_circle = lvl_circle.resize((lvl_circle_dia, lvl_circle_dia), Image.ANTIALIAS)
        lvl_bar_mask = mask.resize((lvl_circle_dia, lvl_circle_dia), Image.ANTIALIAS)
        process.paste(lvl_circle, (circle_left, circle_top), lvl_bar_mask)

        # draws mask
        total_gap = 10
        border = int(total_gap/2)
        profile_size = lvl_circle_dia - total_gap
        raw_length = profile_size * multiplier
        # put in profile picture
        output = ImageOps.fit(profile_image, (raw_length, raw_length), centering=(0.5, 0.5))
        output = output.resize((profile_size, profile_size), Image.ANTIALIAS)
        mask = mask.resize((profile_size, profile_size), Image.ANTIALIAS)
        profile_image = profile_image.resize((profile_size, profile_size), Image.ANTIALIAS)
        process.paste(profile_image, (circle_left + border, circle_top + border), mask)

        # draw level box
        level_left = 274
        level_right = right_pos
        draw.rectangle([(level_left, vert_pos), (level_right, vert_pos + title_height)], fill="#AAA") # box
        lvl_text = "LEVEL {}".format(userinfo["servers"][server.id]["level"])
        draw.text((self._center(level_left, level_right, lvl_text, level_label_fnt), vert_pos + 3), lvl_text,  font=level_label_fnt, fill=(110,110,110,255)) # Level #

        # labels text colors
        white_text = (240,240,240,255)
        dark_text = (35, 35, 35, 230)
        label_text_color = self._contrast(info_color, white_text, dark_text)

        # draw text
        grey_color = (110,110,110,255)
        white_color = (230,230,230,255)

        # put in server picture
        server_size = content_bottom - content_top - 10
        server_border_size = server_size + 4
        radius = 20
        light_border = (150,150,150,180)
        dark_border = (90,90,90,180)
        border_color = self._contrast(info_color, light_border, dark_border)

        draw_server_border = Image.new('RGBA', (server_border_size*multiplier, server_border_size*multiplier),border_color)
        draw_server_border = self._add_corners(draw_server_border, int(radius*multiplier/2))
        draw_server_border = draw_server_border.resize((server_border_size, server_border_size), Image.ANTIALIAS)
        server_image = server_image.resize((server_size*multiplier, server_size*multiplier), Image.ANTIALIAS)
        server_image = self._add_corners(server_image, int(radius*multiplier/2)-10)
        server_image = server_image.resize((server_size, server_size), Image.ANTIALIAS)
        process.paste(draw_server_border, (circle_left + profile_size + 2*border + 8, content_top + 3), draw_server_border)
        process.paste(server_image, (circle_left + profile_size + 2*border + 10, content_top + 5), server_image)

        # name
        left_text_align = 130
        _write_unicode(self._truncate_text(self._name(user, 20), 20), left_text_align - 12, vert_pos + 3, name_fnt, header_u_fnt, grey_color) # Name

        # divider bar
        draw.rectangle([(187, 45), (188, 85)], fill=(160,160,160,220))

        # labels
        label_align = 200
        draw.text((label_align, 38), "Server Rank:", font=general_info_fnt, fill=label_text_color) # Server Rank
        draw.text((label_align, 58), "Server Exp:", font=general_info_fnt, fill=label_text_color) # Server Exp
        draw.text((label_align, 78), "Credits:", font=general_info_fnt, fill=label_text_color) # Credit
        # info
        right_text_align = 290
        rank_txt = "#{}".format(await self._find_server_rank(user, server))
        draw.text((right_text_align, 38), self._truncate_text(rank_txt, 12) , font=general_info_fnt, fill=label_text_color) # Rank
        exp_txt = "{}".format(await self._find_server_exp(user, server))
        draw.text((right_text_align, 58), self._truncate_text(exp_txt, 12), font=general_info_fnt, fill=label_text_color) # Exp
        try:
            bank = self.bot.get_cog('Economy').bank
            if bank.account_exists(user):
                credits = bank.get_balance(user)
            else:
                credits = 0
        except:
            credits = 0
        credit_txt = "${}".format(credits)
        draw.text((right_text_align, 78), self._truncate_text(credit_txt, 12),  font=general_info_fnt, fill=label_text_color) # Credits

        result = Image.alpha_composite(result, process)
        result.save('data/leveler/temp/{}_rank.png'.format(user.id),'PNG', quality=100)

    def _add_corners(self, im, rad):
        circle = Image.new('L', (rad * 2, rad * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
        alpha = Image.new('L', im.size, 255)
        w, h = im.size
        alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
        alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
        alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
        alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
        im.putalpha(alpha)
        return im

    async def draw_levelup(self, user, server):
        userinfo = db.users.find_one({'user_id':user.id})
        # get urls
        bg_url = userinfo["levelup_background"]
        profile_url = user.avatar_url

        # create image objects
        bg_image = Image
        profile_image = Image

        async with aiohttp.get(bg_url) as r:
            image = await r.content.read()
        with open('data/leveler/temp/{}_temp_level_bg.png'.format(user.id),'wb') as f:
            f.write(image)
        try:
            async with aiohttp.get(profile_url) as r:
                image = await r.content.read()
        except:
            async with aiohttp.get(default_avatar_url) as r:
                image = await r.content.read()
        with open('data/leveler/temp/{}_temp_level_profile.png'.format(user.id),'wb') as f:
            f.write(image)

        bg_image = Image.open('data/leveler/temp/{}_temp_level_bg.png'.format(user.id)).convert('RGBA')
        profile_image = Image.open('data/leveler/temp/{}_temp_level_profile.png'.format(user.id)).convert('RGBA')

        # set canvas
        bg_color = (255,255,255, 0)
        result = Image.new('RGBA', (85, 105), bg_color)
        process = Image.new('RGBA', (85, 105), bg_color)

        # draw
        draw = ImageDraw.Draw(process)

        # puts in background
        bg_image = bg_image.resize((85, 105), Image.ANTIALIAS)
        bg_image = bg_image.crop((0,0, 85, 105))
        result.paste(bg_image, (0,0))

        # draw transparent overlay
        if "levelup_info_color" in userinfo.keys():
            info_color = tuple(userinfo["levelup_info_color"])
            info_color = (info_color[0], info_color[1], info_color[2], 160) # increase transparency
        else:
            info_color = (30, 30 ,30, 160)
        draw.rectangle([(0, 40), (85, 105)], fill=info_color) # info portion
        draw.rectangle([(15, 11), (68, 64)], fill=(255,255,255,160), outline=(100, 100, 100, 100)) # profile rectangle

        # put in profile picture
        profile_size = (50, 50)
        profile_image = profile_image.resize(profile_size, Image.ANTIALIAS)
        process.paste(profile_image, (17, 13))

        # fonts
        level_fnt2 = ImageFont.truetype('data/leveler/fonts/font_bold.ttf', 19)
        level_fnt = ImageFont.truetype('data/leveler/fonts/font_bold.ttf', 26)

        # write label text
        white_text = (240,240,240,255)
        dark_text = (35, 35, 35, 230)
        level_up_text = self._contrast(info_color, white_text, dark_text)
        draw.text((self._center(0, 85, "LEVEL UP!", level_fnt2), 67), "LEVEL UP!", font=level_fnt2, fill=level_up_text) # Level
        lvl_text = "LVL {}".format(userinfo["servers"][server.id]["level"])
        draw.text((self._center(2, 85, lvl_text, level_fnt), 83), lvl_text, font=level_fnt, fill=level_up_text) # Level Number

        result = Image.alpha_composite(result, process)
        result.save('data/leveler/temp/{}_level.png'.format(user.id),'PNG', quality=100)

    async def _handle_on_message(self, message):
        #try:
        text = message.content
        channel = message.channel
        server = message.server
        user = message.author
        # creates user if doesn't exist, bots are not logged.
        await self._create_user(user, server)
        curr_time = time.time()
        userinfo = db.users.find_one({'user_id':user.id})

        if not server or server.id in self.settings["disabled_servers"]:
            return
        if user.bot:
            return

        # check if chat_block exists
        if "chat_block" not in userinfo:
            userinfo["chat_block"] = 0

        if float(curr_time) - float(userinfo["chat_block"]) >= 120 and not any(text.startswith(x) for x in prefix):
            await self._process_exp(message, userinfo, random.randint(15, 20))
            await self._give_chat_credit(user, server)
        #except AttributeError as e:
            #pass

    async def _process_exp(self, message, userinfo, exp:int):
        server = message.author.server
        channel = message.channel
        user = message.author

        # add to total exp
        try:
            required = self._required_exp(userinfo["servers"][server.id]["level"])
            db.users.update_one({'user_id':user.id}, {'$set':{
                "total_exp": userinfo["total_exp"] + exp,
                }})
        except:
            pass
        if userinfo["servers"][server.id]["current_exp"] + exp >= required:
            userinfo["servers"][server.id]["level"] += 1
            db.users.update_one({'user_id':user.id}, {'$set':{
                "servers.{}.level".format(server.id): userinfo["servers"][server.id]["level"],
                "servers.{}.current_exp".format(server.id): userinfo["servers"][server.id]["current_exp"] + exp - required,
                "chat_block": time.time()
                }})
            await self._handle_levelup(user, userinfo, server, channel)
        else:
            db.users.update_one({'user_id':user.id}, {'$set':{
                "servers.{}.current_exp".format(server.id): userinfo["servers"][server.id]["current_exp"] + exp,
                "chat_block": time.time()
                }})

    async def _handle_levelup(self, user, userinfo, server, channel):
        if not isinstance(self.settings["lvl_msg"], list):
            self.settings["lvl_msg"] = []
            fileIO("data/leveler/settings.json", "save", self.settings)

        if server.id in self.settings["lvl_msg"]: # if lvl msg is enabled
            # channel lock implementation
            if "lvl_msg_lock" in self.settings.keys() and server.id in self.settings["lvl_msg_lock"].keys():
                channel_id = self.settings["lvl_msg_lock"][server.id]
                channel = find(lambda m: m.id == channel_id, server.channels)

            server_identifier = "" # super hacky
            name = self._is_mention(user) # also super hacky
            # private message takes precedent, of course
            if "private_lvl_msg" in self.settings and server.id in self.settings["private_lvl_msg"]:
                server_identifier = " on {}".format(server.name)
                channel = user
                name = "You"

            if "text_only" in self.settings and server.id in self.settings["text_only"]:
                await self.bot.send_typing(channel)
                em = discord.Embed(description='**{} just gained a level{}! (LEVEL {})**'.format(name, server_identifier, userinfo["servers"][server.id]["level"]), colour=user.colour)
                await self.bot.send_message(channel, '', embed = em)
            else:
                await self.draw_levelup(user, server)
                await self.bot.send_typing(channel)
                await self.bot.send_file(channel, 'data/leveler/temp/{}_level.png'.format(user.id), content='**{} just gained a level{}!**'.format(name, server_identifier))


    async def _find_server_rank(self, user, server):
        targetid = user.id
        users = []

        for userinfo in db.users.find({}):
            try:
                server_exp = 0
                userid = userinfo["user_id"]
                for i in range(userinfo["servers"][server.id]["level"]):
                    server_exp += self._required_exp(i)
                server_exp += userinfo["servers"][server.id]["current_exp"]
                users.append((userid, server_exp))
            except:
                pass

        sorted_list = sorted(users, key=operator.itemgetter(1), reverse=True)

        rank = 1
        for a_user in sorted_list:
            if a_user[0] == targetid:
                return rank
            rank+=1

    async def _find_server_exp(self, user, server):
        server_exp = 0
        userinfo = db.users.find_one({'user_id':user.id})

        try:
            for i in range(userinfo["servers"][server.id]["level"]):
                server_exp += self._required_exp(i)
            server_exp +=  userinfo["servers"][server.id]["current_exp"]
            return server_exp
        except:
            return server_exp

    async def _find_global_rank(self, user, server):
        users = []

        for userinfo in db.users.find({}):
            try:
                userid = userinfo["user_id"]
                users.append((userid, userinfo["total_exp"]))
            except KeyError:
                pass
        sorted_list = sorted(users, key=operator.itemgetter(1), reverse=True)

        rank = 1
        for stats in sorted_list:
            if stats[0] == user.id:
                return rank
            rank+=1

    # handles user creation, adding new server, blocking
    async def _create_user(self, user, server):
        try:
            userinfo = db.users.find_one({'user_id':user.id})
            if not userinfo:
                new_account = {
                    "user_id" : user.id,
                    "servers": {},
                    "total_exp": 0,
                    "profile_background": self.backgrounds["profile"]["default"],
                    "rank_background": self.backgrounds["rank"]["default"],
                    "levelup_background": self.backgrounds["levelup"]["default"],
                    "title": "",
                    "info": "I am a mysterious person.",
                    "rep": 0,
                    "badges":{},
                    "active_badges":{},
                    "rep_color": [],
                    "badge_col_color": [],
                    "rep_block": 0,
                    "chat_block": 0,
                    "profile_block": 0,
                    "rank_block": 0
                }
                db.users.insert_one(new_account)

            userinfo = db.users.find_one({'user_id':user.id})
            if "servers" not in userinfo or server.id not in userinfo["servers"]:
                db.users.update_one({'user_id':user.id}, {'$set':{
                        "servers.{}.level".format(server.id): 0,
                        "servers.{}.current_exp".format(server.id): 0,
                    }}, upsert = True)
        except AttributeError as e:
            pass

    def _truncate_text(self, text, max_length):
        if len(text) > max_length:
            if text.strip('$').isdigit():
                text = int(text.strip('$'))
                return "${:.2E}".format(text)
            return text[:max_length-3] + "..."
        return text

    # finds the the pixel to center the text
    def _center(self, start, end, text, font):
        dist = end - start
        width = font.getsize(text)[0]
        start_pos = start + ((dist-width)/2)
        return int(start_pos)

    # calculates required exp for next level
    def _required_exp(self, level:int):
        if level < 0:
            return 0
        return 139*level+65

    def _level_exp(self, level: int):
        return level*65 + 139*level*(level-1)//2
# ------------------------------ setup ----------------------------------------
def check_folders():
    if not os.path.exists("data/leveler"):
        print("Creating data/leveler folder...")
        os.makedirs("data/leveler")

    if not os.path.exists("data/leveler/temp"):
        print("Creating data/leveler/temp folder...")
        os.makedirs("data/leveler/temp")

def transfer_info():
    try:
        users = fileIO("data/leveler/users.json", "load")
        for user_id in users:
            os.makedirs("data/leveler/users/{}".format(user_id))
            # create info.json
            f = "data/leveler/users/{}/info.json".format(user_id)
            if not fileIO(f, "check"):
                fileIO(f, "save", users[user_id])
    except:
        pass

def check_files():
    default = {
        "bg_price": 0,
        "lvl_msg": [], # enabled lvl msg servers
        "disabled_servers": [],
        "badge_type": "circles",
        "mention" : True,
        "text_only": [],
        "rep_cooldown": 43200,
        "chat_cooldown": 120
        }

    settings_path = "data/leveler/settings.json"
    if not os.path.isfile(settings_path):
        print("Creating default leveler settings.json...")
        fileIO(settings_path, "save", default)

    bgs = {
            "profile": {
                "alice": "http://i.imgur.com/MUSuMao.png",
                "bluestairs": "http://i.imgur.com/EjuvxjT.png",
                "lamp": "http://i.imgur.com/0nQSmKX.jpg",
                "coastline": "http://i.imgur.com/XzUtY47.jpg",
                "redblack": "http://i.imgur.com/74J2zZn.jpg",
                "default": "http://i.imgur.com/8T1FUP5.jpg",
                "iceberg": "http://i.imgur.com/8KowiMh.png",
                "miraiglasses": "http://i.imgur.com/2Ak5VG3.png",
                "miraikuriyama": "http://i.imgur.com/jQ4s4jj.png",
                "mountaindawn": "http://i.imgur.com/kJ1yYY6.jpg",
                "waterlilies": "http://i.imgur.com/qwdcJjI.jpg",
                "greenery": "http://i.imgur.com/70ZH6LX.png"
            },
            "rank": {
                "aurora" : "http://i.imgur.com/gVSbmYj.jpg",
                "default" : "http://i.imgur.com/SorwIrc.jpg",
                "nebula": "http://i.imgur.com/V5zSCmO.jpg",
                "mountain" : "http://i.imgur.com/qYqEUYp.jpg",
                "abstract" : "http://i.imgur.com/70ZH6LX.png",
                "city": "http://i.imgur.com/yr2cUM9.jpg",
            },
            "levelup": {
                "default" : "http://i.imgur.com/eEFfKqa.jpg",
            },
        }

    bgs_path = "data/leveler/backgrounds.json"
    if not os.path.isfile(bgs_path):
        print("Creating default leveler backgrounds.json...")
        fileIO(bgs_path, "save", bgs)

    f = "data/leveler/badges.json"
    if not fileIO(f, "check"):
        print("Creating badges.json...")
        fileIO(f, "save", {})

def setup(bot):
    check_folders()
    check_files()
    n = Leveler(bot)

    bot.add_listener(n._handle_on_message, "on_message")
    bot.add_cog(n)