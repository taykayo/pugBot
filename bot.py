import discord
from discord.ext import commands
from pug import Pug, Team

TOKEN = "NTgyOTM0MDE0MzE1MjAwNTEy.XO1B6A.-PtyJB_3TfKiIRS5bzS75rh8Qj4"

description = "this is a meme bot for soopraball puggers only"

bot = commands.Bot(command_prefix='!', description=description)

pug_list = {}


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')



@bot.command()
async def prefix(ctx, new_prefix: str):
    bot.command_prefix = new_prefix
    await ctx.send(f"Command Prefix changed to: {bot.command_prefix}")

@bot.command()
async def start(ctx, pug_size: int):
    global pug_list
    guild = ctx.guild.id
    channel = ctx.channel.name
    guild_channel_string = str(guild)+'-'+str(channel)

    if guild_channel_string in pug_list.keys():
        await ctx.send(f"<@{ctx.author.id}> There is already an ongoing pug in this channel.")
    else:
        if pug_size == 3 or pug_size == 5:
            blue_team = Team(pug_size, "Blue")
            red_team = Team(pug_size, "Red")
            pug = Pug(pug_size)
            pug_list[guild_channel_string] = pug

            await ctx.send(f"{pug.pug_status('Pug has started.')}")

        else:
            await ctx.send(f"Invalid Pug Size")


@bot.command(aliases=["list", "players"])
async def status(ctx):
    guild = ctx.guild.id
    channel = ctx.channel.name
    guild_channel_string = str(guild)+'-'+str(channel)
    pug = pug_list[guild_channel_string]
    await ctx.send(pug.pug_status(''))


@bot.command()
async def aadd(ctx, user: str, position: str):
    try:
        guild = ctx.guild.id
        channel = ctx.channel.name
        guild_channel_string = str(guild)+'-'+str(channel)
        pug = pug_list[guild_channel_string]
    except KeyError:
        await ctx.send(f"<@{ctx.author.id}> No pug in progress. Use the !start command to launch a pug. ")
        return
    user_id = ''.join(filter(lambda x: x.isdigit(), user))  # filters out non-digits
    disc_user = ctx.guild.get_member(int(user_id))
    status_msg = ''
    if position in ["m", "M", "mid", "MID", "Mid"]:
        if disc_user in pug.mid:
            await ctx.send(f"<@{ctx.author.id}> {str(disc_user.name)} is already added to this position.")
        else:
            if (disc_user in pug.defs) or (disc_user in pug.keep):
                pug.remove_player(disc_user)
            if len(pug.mid) >= pug.mid_limit:
                await ctx.send(f"<@{ctx.author.id}> This position is full.")
            else:
                pug.add_player(disc_user, "mid")
                status_msg = f"{str(disc_user.name)} has been signed up as a midfielder."

    elif position in ["k", "K", "keep", "Keep", "KEEP"]:
        if disc_user in pug.keep:
            await ctx.send(f"<@{ctx.author.id}> {str(disc_user.name)} is already added to this position.")
        else:
            if (disc_user in pug.defs) or (disc_user in pug.mid):
                pug.remove_player(disc_user)
            if len(pug.keep) >= pug.keep_limit:
                await ctx.send(f"<@{ctx.author.id}> This position is full.")
            else:
                pug.add_player(disc_user, "keep")
                status_msg = f"{str(disc_user.name)} has been signed up as a keeper."

    elif position in ["d", "D", "def", "Def", "Defender", "defender", "DEFENDER"]:
        if disc_user in pug.mid:
            await ctx.send(f"<@{ctx.author.id}> {str(disc_user.name)} is already added to this position.")
        else:
            if (disc_user in pug.mid) or (disc_user in pug.keep):
                pug.remove_player(disc_user)
            if len(pug.defs) >= pug.def_limit:
                await ctx.send(f"<@{ctx.author.id}> This position is full.")
            else:
                pug.add_player(disc_user, "defs")
                status_msg = f"{str(disc_user.name)} signed up as a defender."

    else:
        await ctx.send(f"<@{ctx.author.id}> Invalid position.")
    await ctx.send(pug.pug_status(status_msg))

@bot.command()
async def aremove(ctx, user: str):
    try:
        guild = ctx.guild.id
        channel = ctx.channel.name
        guild_channel_string = str(guild)+'-'+str(channel)
        pug = pug_list[guild_channel_string]
    except KeyError:
        await ctx.send(f"<@{ctx.author.id}> No pug in progress. Use the !start command to launch a pug. ")
        return
    user_id = ''.join(filter(lambda x: x.isdigit(), user))  # filters out non-digits
    disc_user = ctx.guild.get_member(int(user_id))

    if disc_user in pug.mid:
        pug.remove_player(disc_user)
        status_msg = f"{str(disc_user.name)} has been removed from the pug"
    elif disc_user in pug.keep:
        pug.remove_player(disc_user)
        status_msg = f"{str(disc_user.name)} has been removed from the pug"
    elif disc_user in pug.defs:
        pug.remove_player(disc_user)
        status_msg = f"{str(disc_user.name)} has been removed from the pug"
    else:
        await ctx.send(f"<@{ctx.author.id}> {str(disc_user.name)} is not signed up for this pug.")
        return
    await ctx.send(pug.pug_status(status_msg))


@bot.command()
async def remove(ctx):
    try:
        guild = ctx.guild.id
        channel = ctx.channel.name
        guild_channel_string = str(guild)+'-'+str(channel)
        pug = pug_list[guild_channel_string]
    except KeyError:
        await ctx.send(f"<@{ctx.author.id}> No pug in progress. Use the !start command to launch a pug. ")
        return
    disc_user = ctx.author

    if disc_user in pug.mid:
        pug.remove_player(disc_user)
        status_msg = f"{str(disc_user.name)} has been removed from the pug"
    elif disc_user in pug.keep:
        pug.remove_player(disc_user)
        status_msg = f"{str(disc_user.name)} has been removed from the pug"
    elif disc_user in pug.defs:
        pug.remove_player(disc_user)
        status_msg = f"{str(disc_user.name)} has been removed from the pug"
    else:
        await ctx.send(f"<@{ctx.author.id}> {str(disc_user.name)} is not signed up for this pug.")
        return
    await ctx.send(pug.pug_status(status_msg))

bot.run('NTgyOTM0MDE0MzE1MjAwNTEy.XO1B6A.-PtyJB_3TfKiIRS5bzS75rh8Qj4')
