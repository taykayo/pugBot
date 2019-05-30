import random
from discord.ext import commands
from pug import Pug, Team
import configparser
config = configparser.ConfigParser()
config.read('config.ini')
TOKEN = config['config']['bot_token']
PugAdmin = config['config']['PugbotAdmin']
description = "this is a meme bot for soopraball puggers only"

bot = commands.Bot(command_prefix='!', description=description)

pug_list = {}
team_list = {}


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command(name="Prefix", help="Used to change the bot command prefix.", usage="[prefix]",
             description="Used to change the bot command prefix.", aliases=["prefix"])
@commands.has_role("Pugbot Overlord")
async def prefix(ctx, new_prefix: str):
    bot.command_prefix = new_prefix
    await ctx.send(f"Command Prefix changed to: {bot.command_prefix}")


@bot.command(name="Start", brief="Starts a channel specific pug queue",
             help="This command starts a channel specific pug which users can queue for. ""Users will be notified"
                  " once the pug has reached the required amount of players.  This works with both 3v3 and 5v5 pugs.",
             usage="[3|5]",
             description="Instantiates the pug class specific to server-channel, allows users to add to queue. "
                         " Once queue has reach capacity, pug changes to picking state, instantiate two teams "
                         "(blue and red). Shuts itself down once teams are picked.",
             aliases=["start", "START"])
async def start(ctx, pug_size: int):
    global pug_list
    guild = ctx.guild.id
    channel = ctx.channel.name
    guild_channel_string = str(guild)+'-'+str(channel)

    if guild_channel_string in pug_list.keys():
        await ctx.send(f"<@{ctx.author.id}> There is already an ongoing pug in this channel.")
    else:
        if pug_size == 3 or pug_size == 5:
            pug = Pug(pug_size)
            pug_list[guild_channel_string] = pug

            await ctx.send(f"{pug.pug_status('Pug has started.')}")

        else:
            await ctx.send(f"Invalid Pug Size")


@bot.command(name="Stop", aliases=["stop", "STOP"], help="Used to stop a pug match", description="Unregisters the current pug from the list of"
                                                                       "running pug matches (stored in a dictionary"
                                                                       "where the key is 'server-channel', attempts to"
                                                                       "unregister the teams as well if pug was in"
                                                                       "picking phase.", pass_context=True)
@commands.has_role(PugAdmin)
async def stop(ctx):
    global pug_list, team_list
    try:
        guild = ctx.guild.id
        channel = ctx.channel.name
        guild_channel_string = str(guild)+'-'+str(channel)
        pug = pug_list[guild_channel_string]
        del pug_list[guild_channel_string]
        del pug
        try:
            del team_list[guild_channel_string + '-blue']
            del team_list[guild_channel_string + '-red']
        except:
            pass

        await ctx.send(f"<@{ctx.author.id}> Pug has been stopped. ")
    except KeyError:
        await ctx.send(f"<@{ctx.author.id}> No pug in progress. Use the !start command to launch a pug. ")
        return


@bot.command(aliases=["list", "status", "players"], name="Status")
async def status(ctx):
    try:
        guild = ctx.guild.id
        channel = ctx.channel.name
        guild_channel_string = str(guild)+'-'+str(channel)
        pug = pug_list[guild_channel_string]
        if pug.state == 1:

            blue_team = team_list[guild_channel_string + '-blue']
            red_team = team_list[guild_channel_string + '-red']
            await ctx.send(pug.pug_status('', blue_team, red_team))
        else:
            await ctx.send(pug.pug_status(''))
    except KeyError:
        await ctx.send(f"<@{ctx.author.id}> No pug in progress. Use the !start command to launch a pug. ")


@bot.command(name="Admin Add", aliases=["aadd", "AADD", "aADD", "Aadd"], help="Usable by admins to force add a "
                                                                                      "user to the pug queue.",
             usage="[@user] [position]")
@commands.has_role(PugAdmin)
async def aadd(ctx, user: str, position: str):
    try:
        guild = ctx.guild.id
        channel = ctx.channel.name
        guild_channel_string = str(guild)+'-'+str(channel)
        pug = pug_list[guild_channel_string]
    except KeyError:
        await ctx.send(f"<@{ctx.author.id}> No pug in progress. Use the !start command to launch a pug. ")
        return
    if pug.state == 1:
        await ctx.send(f"<@{ctx.author.id}> Cannot add or remove during pick phase!")
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
                if pug.state == 0:
                    await ctx.send(pug.pug_status(status_msg))

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
                if pug.state == 0:
                    await ctx.send(pug.pug_status(status_msg))

    elif position in ["d", "D", "def", "Def", "Defender", "defender", "DEFENDER"]:
        if disc_user in pug.defs:
            await ctx.send(f"<@{ctx.author.id}> {str(disc_user.name)} is already added to this position.")
        else:
            if (disc_user in pug.mid) or (disc_user in pug.keep):
                pug.remove_player(disc_user)
            if len(pug.defs) >= pug.def_limit:
                await ctx.send(f"<@{ctx.author.id}> This position is full.")
            else:
                pug.add_player(disc_user, "defs")
                status_msg = f"{str(disc_user.name)} has been signed up as a defender."
                if pug.state == 0:
                    await ctx.send(pug.pug_status(status_msg))

    else:
        await ctx.send(f"<@{ctx.author.id}> Invalid position.")
    if pug.state == 1:
        await start_picking(ctx)


@bot.command(aliases=["a"])
async def add(ctx, position: str):
    try:
        guild = ctx.guild.id
        channel = ctx.channel.name
        guild_channel_string = str(guild)+'-'+str(channel)
        pug = pug_list[guild_channel_string]
    except KeyError:
        await ctx.send(f"<@{ctx.author.id}> No pug in progress. Use the !start command to launch a pug. ")
        return
    if pug.state == 1:
        await ctx.send(f"<@{ctx.author.id}> Cannot add or remove during pick phase!")
        return
    disc_user = ctx.author
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
                status_msg = f"{str(disc_user.name)} has signed up as a midfielder."
                if pug.state == 0:
                    await ctx.send(pug.pug_status(status_msg))

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
                status_msg = f"{str(disc_user.name)} has signed up as a keeper."
                if pug.state == 0:
                    await ctx.send(pug.pug_status(status_msg))

    elif position in ["d", "D", "def", "Def", "Defender", "defender", "DEFENDER"]:
        if disc_user in pug.defs:
            await ctx.send(f"<@{ctx.author.id}> {str(disc_user.name)} is already added to this position.")
        else:
            if (disc_user in pug.mid) or (disc_user in pug.keep):
                pug.remove_player(disc_user)
            if len(pug.defs) >= pug.def_limit:
                await ctx.send(f"<@{ctx.author.id}> This position is full.")
            else:
                pug.add_player(disc_user, "defs")
                status_msg = f"{str(disc_user.name)} has signed up as a defender."
                if pug.state == 0:
                    await ctx.send(pug.pug_status(status_msg))

    else:
        await ctx.send(f"<@{ctx.author.id}> Invalid position.")
    if pug.state ==1:
        await start_picking(ctx)


@bot.command()
@commands.has_role(PugAdmin)
async def aremove(ctx, user: str):
    try:
        guild = ctx.guild.id
        channel = ctx.channel.name
        guild_channel_string = str(guild)+'-'+str(channel)
        pug = pug_list[guild_channel_string]
    except KeyError:
        await ctx.send(f"<@{ctx.author.id}> No pug in progress. Use the !start command to launch a pug. ")
        return
    if pug.state == 1:
        await ctx.send(f"<@{ctx.author.id}> Cannot add or remove during pick phase!")
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
    if pug.state == 1:
        await ctx.send(f"<@{ctx.author.id}> Cannot add or remove during pick phase!")
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


async def start_picking(ctx):
    guild = ctx.guild.id
    channel = ctx.channel.name
    guild_channel_string = str(guild) + '-' + str(channel)
    pug = pug_list[guild_channel_string]

    blue_team = Team(pug.pug_size, "Blue")
    red_team = Team(pug.pug_size, "Red")
    team_list[guild_channel_string + '-blue'] = blue_team
    team_list[guild_channel_string + '-red'] = red_team


    status_msg = 'Picking has started.'
    if pug.pug_size == 5:
        if random.randint(0, 1) == 0:
            if random.randint(0, 1) == 0:  # keeper captains
                blue_team.add_player("keep", pug.keep[1])
                red_team.add_player("keep", pug.keep[0])
                blue_team.captain = pug.keep.pop(1)
                red_team.captain = pug.keep.pop(0)
            else:
                blue_team.add_player("keep", pug.keep[0])
                red_team.add_player("keep", pug.keep[1])
                blue_team.captain = pug.keep.pop(0)
                red_team.captain = pug.keep.pop(0)
        else:  # defender captains
            if random.randint(0, 1) == 0:
                blue_team.add_player("defs", pug.defs[1])
                red_team.add_player("defs", pug.defs[0])
                blue_team.captain = pug.defs.pop(1)
                red_team.captain = pug.defs.pop(0)
            else:
                blue_team.add_player("defs", pug.defs[0])
                red_team.add_player("defs", pug.defs[1])
                blue_team.captain = pug.defs.pop(0)
                red_team.captain = pug.defs.pop(0)
    else:
        if random.randint(0, 1) == 0:  # keeper captains
            blue_team.add_player("keep", pug.keep[1])
            red_team.add_player("keep", pug.keep[0])
            blue_team.captain = pug.keep.pop(1)
            red_team.captain = pug.keep.pop(0)
        else:
            blue_team.add_player("keep", pug.keep[0])
            red_team.add_player("keep", pug.keep[1])
            blue_team.captain = pug.keep.pop(0)
            red_team.captain = pug.keep.pop(0)

    await ctx.send(pug.pug_status(status_msg, blue_team, red_team))


@bot.command()
@commands.has_role(PugAdmin)
async def apick(ctx, user):
    global pug_list, team_list
    try:
        guild = ctx.guild.id
        channel = ctx.channel.name
        guild_channel_string = str(guild)+'-'+str(channel)
        pug = pug_list[guild_channel_string]
        user_id = ''.join(filter(lambda x: x.isdigit(), user))  # filters out non-digits
        disc_user = ctx.guild.get_member(int(user_id))
        blue_team = team_list[guild_channel_string + '-blue']
        red_team = team_list[guild_channel_string + '-red']

    except KeyError:
        await ctx.send(f"<@{ctx.author.id}> No pug in progress. Use the !start command to launch a pug. ")
        return

    if pug.state == 0:
        await ctx.send(f"<@{ctx.author.id}> Pug not in pick phase.")
        return
    if pug.pick_order[pug.next_pick] == 1:

            if (disc_user in pug.mid) or (disc_user in pug.keep) or ( disc_user in pug.defs):
                status_msg = f"{str(disc_user.name)} has been picked by **BLUE TEAM**"
                pug.team_pick(blue_team, disc_user)

                if (len(blue_team.defs) == blue_team.defs_limit) and (len(pug.defs) > 0):
                    status_msg += f"\n{str(pug.defs[0].name)} has been auto-assigned to **RED TEAM**"
                    pug.team_pick(red_team, pug.defs[0], False)
                    del pug.pick_order[-1]
                if (len(blue_team.keep) == blue_team.keep_limit) and (len(pug.keep) > 0):
                    status_msg += f"\n{str(pug.keep[0].name)} has been auto-assigned to **RED TEAM**"
                    pug.team_pick(red_team, pug.keep[0], False)
                    del pug.pick_order[-1]
                while len(blue_team.mid) == blue_team.mid_limit and (len(pug.mid) > 0):
                    status_msg += f"\n{str(pug.mid[0].name)} has been auto-assigned to **RED TEAM**"
                    pug.team_pick(red_team, pug.mid[0], False)
                    del pug.pick_order[-1]
                await ctx.send(pug.pug_status(status_msg, blue_team, red_team))
                if pug.state == 2:
                    del pug_list[guild_channel_string]
                    del pug
                    try:
                        del team_list[guild_channel_string + '-blue']
                        del team_list[guild_channel_string + '-red']
                    except:
                        pass

            else:
                await ctx.send(f"<@{ctx.author.id}> {str(disc_user.name)} is not a valid choice. Please pick a valid player.")

    elif pug.pick_order[pug.next_pick] == 2:
            if (disc_user in pug.mid) or (disc_user in pug.keep) or (disc_user in pug.defs):
                status_msg = f"{str(disc_user.name)} has been picked by **RED TEAM**"
                pug.team_pick(red_team, disc_user)

                if (len(red_team.defs) == red_team.defs_limit) and (len(pug.defs) > 0):
                    status_msg += f"\n{str(pug.defs[0].name)} has been auto-assigned to **BLUE TEAM**"
                    pug.team_pick(blue_team, pug.defs[0], False)
                    del pug.pick_order[-1]
                if (len(red_team.keep) == red_team.keep_limit) and (len(pug.keep) > 0):
                    status_msg += f"\n{str(pug.keep[0].name)} has been auto-assigned to **BLUE TEAM**"
                    pug.team_pick(blue_team, pug.keep[0], False)
                    del pug.pick_order[-1]
                while (len(red_team.mid) == red_team.mid_limit) and (len(pug.mid) > 0):
                    status_msg += f"\n{str(pug.mid[0].name)} has been auto-assigned to **BLUE TEAM**"
                    pug.team_pick(blue_team, pug.mid[0], False)
                    del pug.pick_order[-1]
                await ctx.send(pug.pug_status(status_msg, blue_team, red_team))
                if pug.state == 2:
                    del pug_list[guild_channel_string]
                    del pug
                    try:
                        del team_list[guild_channel_string + '-blue']
                        del team_list[guild_channel_string + '-red']
                    except:
                        pass

            else:
                status_msg = f"{str(disc_user.name)} is not in the pug.**"
                await ctx.send(pug.pug_status(status_msg, blue_team, red_team))
    else:
        await ctx.send(f"something done borked")


@bot.command()
async def pick(ctx, user):
    global pug_list, team_list
    try:
        guild = ctx.guild.id
        channel = ctx.channel.name
        guild_channel_string = str(guild)+'-'+str(channel)
        pug = pug_list[guild_channel_string]
        user_id = ''.join(filter(lambda x: x.isdigit(), user))  # filters out non-digits
        disc_user = ctx.guild.get_member(int(user_id))
        blue_team = team_list[guild_channel_string + '-blue']
        red_team = team_list[guild_channel_string + '-red']

    except KeyError:
        await ctx.send(f"<@{ctx.author.id}> No pug in progress. Use the !start command to launch a pug. ")
        return

    if pug.state == 0:
        await ctx.send(f"<@{ctx.author.id}> Pug not in pick phase.")
        return
    if pug.pick_order[pug.next_pick] == 1:

        if ctx.author == blue_team.captain:
            if (disc_user in pug.mid) or (disc_user in pug.keep) or ( disc_user in pug.defs):
                status_msg = f"{str(disc_user.name)} has been picked by **BLUE TEAM**"
                pug.team_pick(blue_team, disc_user)

                if (len(blue_team.defs) == blue_team.defs_limit) and (len(pug.defs) > 0):
                    status_msg += f"\n{str(pug.defs[0].name)} has been auto-assigned to **RED TEAM**"
                    pug.team_pick(red_team, pug.defs[0], False)
                    del pug.pick_order[-1]
                if (len(blue_team.keep) == blue_team.keep_limit) and (len(pug.keep) > 0):
                    status_msg += f"\n{str(pug.keep[0].name)} has been auto-assigned to **RED TEAM**"
                    pug.team_pick(red_team, pug.keep[0], False)
                    del pug.pick_order[-1]
                while len(blue_team.mid) == blue_team.mid_limit and (len(pug.mid) > 0):
                    status_msg += f"\n{str(pug.mid[0].name)} has been auto-assigned to **RED TEAM**"
                    pug.team_pick(red_team, pug.mid[0], False)
                    del pug.pick_order[-1]
                await ctx.send(pug.pug_status(status_msg, blue_team, red_team))
                if pug.state == 2:
                    del pug_list[guild_channel_string]
                    del pug
                    try:
                        del team_list[guild_channel_string + '-blue']
                        del team_list[guild_channel_string + '-red']
                    except:
                        pass

            else:
                await ctx.send(f"<@{ctx.author.id}> {str(disc_user.name)} is not a valid choice. Please pick a valid player.")


        else:
            await ctx.send(f"<@{ctx.author.id}> Look at me! {blue_team.captain.name} is the captain now!")

    elif pug.pick_order[pug.next_pick] == 2:
        if ctx.author == red_team.captain:
            if (disc_user in pug.mid) or (disc_user in pug.keep) or (disc_user in pug.defs):
                status_msg = f"{str(disc_user.name)} has been picked by **RED TEAM**"
                pug.team_pick(red_team, disc_user)

                if (len(red_team.defs) == red_team.defs_limit) and (len(pug.defs) > 0):
                    status_msg += f"\n{str(pug.defs[0].name)} has been auto-assigned to **BLUE TEAM**"
                    pug.team_pick(blue_team, pug.defs[0], False)
                    del pug.pick_order[-1]
                if (len(red_team.keep) == red_team.keep_limit) and (len(pug.keep) > 0):
                    status_msg += f"\n{str(pug.keep[0].name)} has been auto-assigned to **BLUE TEAM**"
                    pug.team_pick(blue_team, pug.keep[0], False)
                    del pug.pick_order[-1]
                while (len(red_team.mid) == red_team.mid_limit) and (len(pug.mid) > 0):
                    status_msg += f"\n{str(pug.mid[0].name)} has been auto-assigned to **BLUE TEAM**"
                    pug.team_pick(blue_team, pug.mid[0], False)
                    del pug.pick_order[-1]
                await ctx.send(pug.pug_status(status_msg, blue_team, red_team))
                if pug.state == 2:
                    del pug_list[guild_channel_string]
                    del pug
                    try:
                        del team_list[guild_channel_string + '-blue']
                        del team_list[guild_channel_string + '-red']
                    except:
                        pass

            else:
                status_msg = f"{str(disc_user.name)} is not in the pug.**"
                await ctx.send(pug.pug_status(status_msg, blue_team, red_team))

        else:
            await ctx.send(f"<@{ctx.author.id}> Look at me! {red_team.captain.name} is the captain now!")
    else:
        await ctx.send(f"something done borked")

@bot.command()
@commands.has_role(PugAdmin)
async def spo(ctx, pickorder: str):

    try:
        guild = ctx.guild.id
        channel = ctx.channel.name
        guild_channel_string = str(guild)+'-'+str(channel)
        pug = pug_list[guild_channel_string]

    except KeyError:
        await ctx.send(f"<@{ctx.author.id}> No pug in progress. Use the !start command to launch a pug. ")
        return
    if pug.pug_size != 5:
        await ctx.send(f"<@{ctx.author.id}> Cannot change pick order on 3v3 matches.")
        return
    try:
        blue_team = team_list[guild_channel_string + '-blue']
        red_team = team_list[guild_channel_string + '-red']
        await ctx.send(f"<@{ctx.author.id}> Cannot change pick order once picking is in progress")
        return
    except KeyError:
        pass

    if pickorder.lower() == "blitz":
        pug.spo(pickorder)
    elif pickorder.lower() == "normal":
        pug.spo(pickorder)
    elif pickorder.lower() == "linear":
        pug.spo(pickorder)
    else:
        pass
    await ctx.send(pug.pug_status("Pick Order Changed"))


@spo.error
@aremove.error
@apick.error
@aadd.error
@stop.error
async def role_error(ctx, error):
    if isinstance(error,  commands.MissingRole):
        await ctx.send(f"<@{ctx.author.id}> You do not have permission to use this command. ")
bot.run(TOKEN)
