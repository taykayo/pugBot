import random
import discord
from discord.ext import commands
from pug import Pug, PugTeam, ScrimTeamReg, ScrimTeam, Scrim
import configparser
import traceback
import sys

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
config = configparser.ConfigParser()
config.optionxform = str
config.read("config.ini")
TOKEN = config["config"]["bot_token"]
PugAdmin = config["config"]["PugbotAdmin"]
description = "The NA Supraball PugBot, brought to you by Tiny Turtle"
DEBUG = config["config"].getboolean("DEBUG")
bot = commands.Bot(command_prefix="!", description=description, intents=intents)

pugs = dict()
teams = dict()
team_create = dict()


async def start_picking(ctx):
    def pick_captains():
        if pug.pug_size == 5:
            if pug.captains is None:
                if random.randint(0, 1) == 0:
                    position = pug.keep
                    position_string = "keep"
                else:
                    position = pug.defs
                    position_string = "defs"
            elif pug.captains == "d":
                position = pug.defs
                position_string = "defs"
            else:
                position = pug.keep
                position_string = "keep"
        else:
            position = pug.keep
            position_string = "keep"
        weight = random.randint(0, 1)
        blue_team.add_player(position_string, position[1-weight])
        red_team.add_player(position_string, position[weight])
        blue_team.captain = position.pop(1-weight)
        red_team.captain = position.pop(0)

    guild = ctx.guild.id
    channel = ctx.channel.name
    guild_channel_string = str(guild) + "-" + str(channel)
    pug = pugs[guild_channel_string]

    blue_team = PugTeam(pug.pug_size, "Blue")
    red_team = PugTeam(pug.pug_size, "Red")
    teams[guild_channel_string + "-blue"] = blue_team
    teams[guild_channel_string + "-red"] = red_team

    status_msg = "Picking has started."
    if not DEBUG:
        for member in pug.mids + pug.defs + pug.keep:
            await member.send("The pug you signed up has started. Teams will be picked very soon.")

    pick_captains()
    await ctx.send(pug.pug_status(status_msg, blue_team, red_team))


async def attempt_add(ctx, game, disc_user, position):
    global pugs
    # Initialize which position user is attempting to add to
    if position.lower() in ("m", "mid"):
        position = game.mids
        position_limit = game.mid_limit
        position_string = "mid"
        position_status = "midfielder"
    elif position.lower() in ("k", "keep"):
        position = game.keep
        position_limit = game.keep_limit
        position_string = "keep"
        position_status = "keeper"
    elif position.lower() in ("d", "def", "defender"):
        position = game.defs
        position_limit = game.def_limit
        position_string = "defs"
        position_status = "defender"
    else:
        await ctx.send(f"<@{ctx.author.id}> Invalid position.")
        return

    unused = [game.mids, game.defs, game.keep]
    unused.remove(position)  # The positions the user is not adding to
    if disc_user in position:
        await ctx.send(f"<@{ctx.author.id}> {disc_user.name} is already added to this position.")
    else:
        if len(position) >= position_limit:
            await ctx.send(f"<@{ctx.author.id}> This position is full.")
        else:
            status_msg = f"{disc_user.name} has been signed up as a {position_status}."
            if any((disc_user in x) for x in unused):  # checks if user is already signed up for another position
                game.remove_player(disc_user)
                status_msg = f"{disc_user.name} has switched to {position_status}."  # Overwrite signup message with Switch message
            game.add_player(disc_user, position_string)
            to_pick = game.check_player_count()
            if game.state == 0:  # still in signup phase
                await ctx.send(game.pug_status(status_msg))
            elif to_pick == 0:
                await ctx.send(game.pug_status(status_msg))
            elif to_pick == 1:  # only if game type is PUG and players were full
                await start_picking(ctx)
            elif to_pick == 2:
                randoTeam = ScrimTeam()
                for player in game.mids:
                    randoTeam.add_player("mid", player)
                randoTeam.add_player("defs", game.defs[0])
                randoTeam.add_player("keep", game.keep[0])
                await ctx.send(game.pug_status(randoTeam))
                destroy_pug(ctx)

            else:
                pass


async def attempt_remove(ctx, game, disc_user):

    if disc_user in game.mids:
        game.remove_player(disc_user)
        to_pick = game.check_player_count()
        status_msg = f"{str(disc_user.name)} has been removed."
    elif disc_user in game.keep:
        game.remove_player(disc_user)
        to_pick = game.check_player_count()
        status_msg = f"{str(disc_user.name)} has been removed."
    elif disc_user in game.defs:
        game.remove_player(disc_user)
        to_pick = game.check_player_count()
        status_msg = f"{str(disc_user.name)} has been removed."
    else:
        await ctx.send(f"<@{ctx.author.id}> {str(disc_user.name)} is not signed up.")
        return
    await ctx.send(game.pug_status(status_msg))


async def attempt_pick(ctx, game, disc_user):
    blue_team, red_team, = [x for x in get_teams(ctx)]
    if game.state == 0:
        await ctx.send(f"<@{ctx.author.id}> Pug not in pick phase.")
        return
    if game.pick_order[game.next_pick] == 1:
        team = blue_team
        opp_team = red_team
        team_string = "BLUE TEAM"
        opp_string = "RED TEAM"
    elif game.pick_order[game.next_pick] == 2:
        team = red_team
        opp_team = blue_team
        team_string = "RED TEAM"
        opp_string = "BLUE TEAM"

    else:
        await ctx.send(f"something done borked, call mr turtle")
        return

    if any(disc_user in x for x in [game.mids, game.keep, game.defs]):
        status_msg = f"{str(disc_user.name)} has been picked by **{team_string}**"
        game.team_pick(team, disc_user)

        if (len(team.defs) == team.defs_limit) and (len(game.defs) > 0):
            status_msg += f"\n{str(game.defs[0].name)} has been auto-assigned to **{opp_string}**"
            game.team_pick(opp_team, game.defs[0], False)
            del game.pick_order[-1]
        if (len(team.keep) == team.keep_limit) and (len(game.keep) > 0):
            status_msg += f"\n{str(game.keep[0].name)} has been auto-assigned to **{opp_string}**"
            game.team_pick(opp_team, game.keep[0], False)
            del game.pick_order[-1]
        while len(team.mids) == team.mid_limit and (len(game.mids) > 0):
            status_msg += f"\n{str(game.mids[0].name)} has been auto-assigned to **{opp_string}**"
            game.team_pick(opp_team, game.mids[0], False)
            del game.pick_order[-1]
        await ctx.send(game.pug_status(status_msg, blue_team, red_team))
        if game.state == 2:
            destroy_pug(ctx)
            try:
                destroy_teams(ctx)
            except:
                pass

    else:
        await ctx.send(
            f"<@{ctx.author.id}> {str(disc_user.name)} is not a valid choice. Please pick a valid player."
        )


def get_pug(ctx):
    guild_channel = f"{ctx.guild.id}-{ctx.channel.name}"
    pug = pugs[guild_channel]
    return pug


def get_teams(ctx):
    guild_channel = f"{ctx.guild.id}-{ctx.channel.name}"
    blue_team = teams[guild_channel + "-blue"]
    red_team = teams[guild_channel + "-red"]

    return [blue_team, red_team]


def get_team(ctx):
    guild_channel = f"{ctx.guild.id}-{ctx.channel.name}"
    team = team_create[guild_channel]

    return team


def destroy_pug(ctx):
    guild_channel = f"{ctx.guild.id}-{ctx.channel.name}"
    pug = pugs[guild_channel]
    del pugs[guild_channel]
    del pug


def destroy_teams(ctx):
    guild_channel = f"{ctx.guild.id}-{ctx.channel.name}"
    del teams[guild_channel + "-blue"]
    del teams[guild_channel + "-red"]


def destroy_team_create(ctx):
    guild_channel = f"{ctx.guild.id}-{ctx.channel.name}"
    del team_create[guild_channel]


class ScrimTeamCommands(commands.Cog):
    def __init__(self):
        self.bot = bot
        self._last_member = None

    @commands.command(
        name="create_team",
        brief="Starts scrim team creation",
        help="Starts a scrim team creation (one per server at a time)",
        usage="No arguments required"
    )
    async def _create_team(self, ctx):
        global team_create
        guild_channel = f"{ctx.guild.id}-{ctx.channel.name}"
        # TODO Should make it check ONLY guild.id so that only one team can be in creation per server at any given time so as not to have race condition both teams saving at same time

        if guild_channel in team_create.keys():
            await ctx.send(f"<@{ctx.author.id}> There is already a team being created in this channel.")
        else:
            pug = ScrimTeamReg()
            team_create[guild_channel] = pug

            await ctx.send(f"{pug.pug_status('Scrim team creation has started.')}")

    @commands.command(
        name="team",
        brief="Displays the team status",
        help="Has 2 uses - If used without arguments, will return the status of current team creation.  If used with"
             " teamname as an argument, will list the players on the specified team (if it exists)",
        aliases=["team_status"],
        usage="<No arguments required|[teamname]>"

    )
    async def _team_status(self, ctx, *args):
        config.read("config.ini")
        if args:
            team_name = " ".join(args)
            if team_name in config:
                team = ScrimTeam()
                for player in config[team_name]:
                    player_obj = discord.Guild.get_member_named(ctx.guild, player)
                    position = config[team_name][player]
                    team.add_player(position, player_obj)
                await ctx.send(f"{team_name}: \n {team.team_string()}")


            else:
                await ctx.send(f"<@{ctx.author.id}> Team does not exist.")

        else:
            try:
                team = get_team(ctx)
                await ctx.send(team.pug_status(""))
            except KeyError:
                await ctx.send(f"<@{ctx.author.id}> No team creation in progress, use !create_team. ")

    @commands.command(
        name="stop_team",
        help="Used to stop team creation",
        usage="No arguments required"
    )
    async def _stop_team(self, ctx):
        global pugs, teams
        try:
            destroy_team_create(ctx)
            await ctx.send(f"<@{ctx.author.id}> Team creation has been ended. ")
        except KeyError:
            await ctx.send(f"<@{ctx.author.id}> No team creation in progress. ")
            return

    @commands.command(
        name="teamlist",
        brief="Displays the list of team names",
        help="Fetches the list of team names from config file",
        aliases=["team_list"],
        usage="No arguments required",
    )
    async def _team_list(self, ctx):
        config.read("config.ini")
        teamlist = '\n- '.join(config.sections()[1:])
        await ctx.send(f"   **Team List:** \n- {teamlist}")

    @commands.command(
        name="tadd",
        usage="<@user> <position>",
        brief="Adds a user to a team creation position",

    )
    async def _tadd(self, ctx, *args):

        try:
            team = get_team(ctx)
            position = args[-1]
            user = " ".join(args[:-1])
            user_id = "".join(x for x in user if x.isdigit())  # filters out non-digits
            disc_user = ctx.guild.get_member(int(user_id))
        except KeyError:
            await ctx.send(f"<@{ctx.author.id}> No team in creation ")
            return
        except ValueError:
            try:
                disc_user = ctx.guild.get_member_named(user)
                if disc_user is None:
                    raise KeyError("Could not find user")
            except KeyError:
                await ctx.send(
                    f"<@{ctx.author.id}> Could not find user.  Please use the @ to mention the user, or be sure to type "
                    "the name out exactly as it appears in their username."
                )
                return
        await attempt_add(ctx, team, disc_user, position)

    @commands.command(
        name="tremove",
        usage="<@user>",
        brief="Removes user from team creation position"
    )
    async def _tremove(self, ctx, *args):
        try:
            team = get_team(ctx)
            user = " ".join(args)
            user_id = "".join(x for x in user if x.isdigit())  # filters out non-digits
            disc_user = ctx.guild.get_member(int(user_id))
        except KeyError:
            await ctx.send(f"<@{ctx.author.id}> No team in creation. ")
            return
        except ValueError:
            try:
                disc_user = ctx.guild.get_member_named(user)
                if disc_user is None:
                    raise KeyError("Could not find user")
            except KeyError:
                await ctx.send(
                    f"<@{ctx.author.id}> Could not find user.  Please use the @ to mention the user, or be sure to type "
                    "the name out exactly as it appears in their username."
                )
                return
        await attempt_remove(ctx, team, disc_user)

    @commands.command(
        name="save",
        brief="Saves the team configuration as 'teammname'",
        usage="<teamname>",
        help="Creates a section (teamname) in the config file with users as the key and position as the value"
    )
    async def _save(self, ctx, *args):
        try:
            team = get_team(ctx)
            teamname = " ".join(args)
        except KeyError:
            await ctx.send(f"<@{ctx.author.id}> No team in creation. ")
            return
        if team.state == 1:
            passfail = team.save(teamname)

            if passfail == 0:
                await ctx.send(
                    f"<@{ctx.author.id}> Team failed to save. Idk why it would fail so tell turtle to figure it out."
                )
            elif passfail == 1:
                await ctx.send(
                    f"<@{ctx.author.id}> Team {teamname} successfully saved!"
                )
                config.read("config.ini")
                destroy_team_create(ctx)
            elif passfail == 2:
                await ctx.send(
                    f"<@{ctx.author.id}> A team with the name {teamname} already exists, please try again with a different team name!"
                )

        else:
            await ctx.send(
                f"<@{ctx.author.id}> Team is not full yet!"
            )


class PugCommands(commands.Cog):
    def __init__(self):
        self.bot = bot
        self._last_member = None

    @commands.command(
        name="start",
        brief="Starts a channel specific pug queue",
        help=(
                "This command starts a channel specific pug which users can queue for. Users will be notified once the pug has "
                "reached the required amount of players. This works with both 3v3 and 5v5 pugs."
        ),
        usage="<3|5|teamname>",
        description=(
                "Instantiates the pug class specific to server-channel, allows users to add to queue. "
                "Once queue has reached capacity, pug changes to picking state, instantiate two teams (blue and red). "
                "Shuts itself down once teams are picked."
        ),
        aliases=["START"],
    )
    async def _start(self, ctx, arg, *args):
        global pugs, config
        config.read("config.ini")
        guild_channel = f"{ctx.guild.id}-{ctx.channel.name}"
        try:
            if len(args) > 0:
                data = arg
                data += " ".join(args)

            else:
                data = arg
        except:
            pass

        if guild_channel in pugs.keys():
            await ctx.send(f"<@{ctx.author.id}> There is already an ongoing game in this channel.")
        else:

            if data in ["3", "5"]:

                pug = Pug(int(data))
                pugs[guild_channel] = pug

                await ctx.send(f"{pug.pug_status('Pug has started.')}")
            elif data in config.sections():

                team = ScrimTeam()
                team.name = data
                for player in config[data]:
                    player_obj = discord.Guild.get_member_named(ctx.guild, player)
                    position = config[data][player]
                    team.add_player(position, player_obj)
                pug = Scrim(team)
                pugs[guild_channel] = pug

                await ctx.send(f"{pug.pug_status('Scrim sign up has started.')}")
            else:

                await ctx.send(
                    f"<@{ctx.author.id}> Invalid argument.  Please input a valid pug size (3/5) or an existing"
                    f" teamname.")

    @commands.command(
        name="stop",
        aliases=["Stop", "STOP"],
        help="Used to stop a pug match",
        description=(
                "Unregisters the current pug from the list of running pug matches (stored in a dictionary where "
                "the key is 'server-channel', attempts to unregister the teams as well if pug was in picking phase."
        ),
        pass_context=True,
    )
    @commands.has_role(PugAdmin)
    async def _stop(self, ctx):
        global pugs, teams
        try:
            destroy_pug(ctx)
            try:
                destroy_teams(ctx)
            except KeyError:
                pass

            await ctx.send(f"<@{ctx.author.id}> Pug has been stopped. ")
        except KeyError:
            await ctx.send(f"<@{ctx.author.id}> No pug in progress. Use the !start command to launch a pug. ")
            return

    @commands.command(
        aliases=["list", "players", "teams"],
        help=(
                "Shows the current status of the pug; users added to the queue, and during pick phase shows teams, "
                "who is picking, and which players are available."
        ),
        name="status",
        brief="Shows the current status of the pug",
    )
    async def _status(self, ctx):
        try:
            pug = get_pug(ctx)
            if pug.state == 1:

                blue_team, red_team, = [x for x in get_teams(ctx)]

                await ctx.send(pug.pug_status("", blue_team, red_team))
            else:
                await ctx.send(pug.pug_status(""))
        except KeyError:
            await ctx.send(f"<@{ctx.author.id}> No pug in progress. Use the !start command to launch a pug. ")

    @commands.command(
        name="aadd",
        aliases=["AADD", "aADD", "Aadd"],
        help="ADMIN ONLY - Force add a user to the pug queue.",
        usage="<@user> <position>",
    )
    @commands.has_role(PugAdmin)
    async def _aadd(self, ctx, *args):

        try:
            pug = get_pug(ctx)
            position = args[-1]
            user = " ".join(args[:-1])
            user_id = "".join(x for x in user if x.isdigit())  # filters out non-digits
            disc_user = ctx.guild.get_member(int(user_id))

        except KeyError:
            await ctx.send(f"<@{ctx.author.id}> No pug in progress. Use the !start command to launch a pug. ")
            return
        except ValueError:
            try:
                disc_user = ctx.guild.get_member_named(user)
                if disc_user is None:
                    raise KeyError("Could not find user")
            except KeyError:
                await ctx.send(
                    f"<@{ctx.author.id}> Could not find user.  Please use the @ to mention the user, or be sure to type "
                    "the name out exactly as it appears in their username."
                )
                return

        if pug.state == 1:
            await ctx.send(f"<@{ctx.author.id}> Cannot add or remove during pick phase!")
            return
        await attempt_add(ctx, pug, disc_user, position)

    @commands.command(
        name="add",
        aliases=["a", "ADD", "A"],
        brief="Used to register oneself for a pug match",
        usage="<m|k|d>",
        help="Used to register oneself for a pug match",
    )
    async def _add(self, ctx, position: str):
        try:

            pug = get_pug(ctx)
        except KeyError:
            await ctx.send(f"<@{ctx.author.id}> No pug in progress. Use the !start command to launch a pug. ")
            return
        if pug.state == 1:
            await ctx.send(f"<@{ctx.author.id}> Cannot add or remove during pick phase!")
            return
        disc_user = ctx.author

        await attempt_add(ctx, pug, disc_user, position)

    @commands.command(
        name="aremove",
        aliases=["AREMOVE", "Aremove"],
        brief="ADMIN ONLY - Force remove a user from the pug",
        help="ADMIN ONLY - Force remove a user from the pug",
        usage="<@user>",
    )
    @commands.has_role(PugAdmin)
    async def _aremove(self, ctx, *args):
        try:
            pug = get_pug(ctx)
            user = " ".join(args)
            user_id = "".join(x for x in user if x.isdigit())  # filters out non-digits
            disc_user = ctx.guild.get_member(int(user_id))
        except KeyError:
            await ctx.send(f"<@{ctx.author.id}> No pug in progress. Use the !start command to launch a pug. ")
            return
        except ValueError:
            try:
                disc_user = ctx.guild.get_member_named(user)
                if disc_user is None:
                    raise KeyError("Could not find user")
            except KeyError:
                await ctx.send(
                    f"<@{ctx.author.id}> Could not find user.  Please use the @ to mention the user, or be sure to type "
                    "the name out exactly as it appears in their username."
                )
                return
        if pug.state == 1:
            await ctx.send(f"<@{ctx.author.id}> Cannot add or remove during pick phase!")
            return

        await attempt_remove(ctx, pug, disc_user)

    @commands.command(
        name="remove",
        aliases=["r", "R", "Remove", "REMOVE"],
        brief="Used to remove oneself from a pug match",
        help="Used to remove oneself from a pug match",
    )
    async def _remove(self, ctx):
        try:
            pug = get_pug(ctx)
        except KeyError:
            await ctx.send(f"<@{ctx.author.id}> No pug in progress. Use the !start command to launch a pug. ")
            return
        if pug.state == 1:
            await ctx.send(f"<@{ctx.author.id}> Cannot add or remove during pick phase!")
            return
        disc_user = ctx.author

        await attempt_remove(ctx, pug, disc_user)

    @commands.command(
        name="apick",
        aliases=["APICK", "Apick"],
        brief="ADMIN ONLY - Force pick a player for the choosing team",
        help="ADMIN ONLY - Force pick a player to join whichever team is currently picking",
        usage="<@user>",
    )
    @commands.has_role(PugAdmin)
    async def _apick(self, ctx, *args):
        global pugs, teams
        try:
            pug = get_pug(ctx)
            blue_team, red_team, = [x for x in get_teams(ctx)]
            user = " ".join(args)
            user_id = "".join(filter(lambda x: x.isdigit(), user))  # filters out non-digits
            disc_user = ctx.guild.get_member(int(user_id))

        except KeyError:
            await ctx.send(f"<@{ctx.author.id}> No picking in progress.")
            return
        except ValueError:
            try:
                disc_user = ctx.guild.get_member_named(user)
                if disc_user is None:
                    raise KeyError("Could not find user")
            except KeyError:
                await ctx.send(
                    f"<@{ctx.author.id}> Could not find user.  Please use the @ to mention the user, or be sure to type "
                    "the name out exactly as it appears in their username."
                )
                return
        await attempt_pick(ctx, pug, disc_user)

    @commands.command(
        name="pick",
        aliases=["PICK", "p", "P", "Pick"],
        brief="Picks a player during pick turn",
        help="Adds specified player to your team.  Only usable by the team captain on their team's pick turn",
        usage="<@user>",
    )
    async def _pick(self, ctx, *args):
        global pugs, teams
        try:
            pug = get_pug(ctx)
            blue_team, red_team, = [x for x in get_teams(ctx)]
            user = " ".join(args)
            user_id = "".join(filter(lambda x: x.isdigit(), user))  # filters out non-digits
            disc_user = ctx.guild.get_member(int(user_id))

        except KeyError:
            await ctx.send(f"<@{ctx.author.id}> No picking in progress.")
            return
        except ValueError:
            try:
                disc_user = ctx.guild.get_member_named(user)
                if disc_user is None:
                    raise KeyError("Could not find user")
            except KeyError:
                await ctx.send(
                    f"<@{ctx.author.id}> Could not find user.  Please use the @ to mention the user, or be sure to type "
                    "the name out exactly as it appears in their username."
                )
                return

        if pug.state == 0:
            await ctx.send(f"<@{ctx.author.id}> Pug not in pick phase.")
            return
        if (pug.pick_order[pug.next_pick] == 1) and not (ctx.author == blue_team.captain):
            await ctx.send(f"<@{ctx.author.id}> Look at me! {blue_team.captain.name} is the captain now!")
            return
        elif pug.pick_order[pug.next_pick] == 2 and not (ctx.author == red_team.captain):
            await ctx.send(f"<@{ctx.author.id}> Look at me! {red_team.captain.name} is the captain now!")
            return
        await attempt_pick(ctx, pug, disc_user)

    @commands.command(
        name="spo",
        aliases=["SPO", "Spo"],
        brief="ADMIN ONLY - Change the pug team pick order",
        help=(
                "ADMIN ONLY - "
                "Changes the pick order to specified setting.  Not available for 3v3 pugs. "
                "Supports NA Normal: [B, R, R, B, R, B, R], Blitz: [B, R, R, B, B, R, B], and Linear: [B, R, B, R, B, R, B]"
        ),
        usage="<Blitz|Linear|Normal>",
    )
    @commands.has_role(PugAdmin)
    async def _spo(self, ctx, pickorder: str):

        try:
            guild = ctx.guild.id
            channel = ctx.channel.name
            guild_channel = str(guild) + "-" + str(channel)
            pug = pugs[guild_channel]
        except KeyError:
            await ctx.send(f"<@{ctx.author.id}> No pug in progress. Use the !start command to launch a pug. ")
            return

        if pug.pug_size != 5:
            await ctx.send(f"<@{ctx.author.id}> Cannot change pick order on 3v3 matches.")
            return

        if f"{guild_channel}-blue" in teams or f"{guild_channel}-red" in teams:
            await ctx.send(f"<@{ctx.author.id}> Cannot change pick order once picking is in progress")
            return

        if pickorder.lower() == "blitz":
            pug.spo(pickorder)
        elif pickorder.lower() == "normal":
            pug.spo(pickorder)
        elif pickorder.lower() == "linear":
            pug.spo(pickorder)
        else:
            await ctx.send(pug.pug_status("Invalid pick order. Valid options are 'normal', 'blitz', or 'linear'."))
        await ctx.send(pug.pug_status("Pick Order Changed"))

    @commands.command(
        name="captains",
        aliases=["Captains", "CAPTAINS", "c", "C", "captain"],
        brief="ADMIN ONLY - Selects which position will be captains.",
        help="ADMIN ONLY - Selects which position will be used for captains.  Not usable in 3v3",
        usage="<k|d|random>",
    )
    @commands.has_role(PugAdmin)
    async def _captains(self, ctx, captains: str):

        try:
            guild = ctx.guild.id
            channel = ctx.channel.name
            guild_channel_string = str(guild) + "-" + str(channel)
            pug = pugs[guild_channel_string]

        except KeyError:
            await ctx.send(f"<@{ctx.author.id}> No pug in progress. Use the !start command to launch a pug. ")
            return
        if pug.pug_size != 5:
            await ctx.send(f"<@{ctx.author.id}> Cannot set captains on 3v3 matches.")
            return
        try:
            # TODO: just use an if statement here (see changes to _spo above)
            blue_team = teams[guild_channel_string + "-blue"]
            red_team = teams[guild_channel_string + "-red"]
            await ctx.send(f"<@{ctx.author.id}> Cannot change captains once picking is in progress.")
            return
        except KeyError:
            pass

        if captains.lower() == "d":
            pug.set_captains(captains.lower())
            await ctx.send(pug.pug_status("Defenders will be captains."))
        elif captains.lower() == "k":
            pug.set_captains(captains.lower())
            await ctx.send(pug.pug_status("Keepers will be captains."))
        elif captains.lower() == "random":
            pug.set_captains(None)
            await ctx.send(pug.pug_status("Captains will be random."))
        else:
            await ctx.send(f"<@{ctx.author.id}> Invalid captain selection. Valid options are 'd', 'k', or 'random'.")


class CommandErrorHandler(commands.Cog):
    def __init__(self):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.
        ctx   : Context
        error : Exception"""

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return

        ignored = (commands.CommandNotFound)

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        elif isinstance(error, commands.DisabledCommand):
            return await ctx.send(f'{ctx.command} has been disabled.')

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.author.send(f'{ctx.command} can not be used in Private Messages.')
            except:
                pass

        elif isinstance(error, commands.MissingRole):
            return await ctx.send(f"<@{ctx.author.id}> You do not have permission to use this command. ")

        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f"<@{ctx.author.id}> Please enter all required arguments. ")


        # All other Errors not returned come here... And we can just print the default TraceBack.
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


bot.add_cog(ScrimTeamCommands())
bot.add_cog(PugCommands())
bot.add_cog(CommandErrorHandler())
@bot.event
async def on_ready():
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("------")


@bot.command(
    name="prefix",
    help="ADMIN ONLY - Used to change the bot command prefix",
    usage="<prefix>",
    description="ADMIN ONLY - Used to change the bot command prefix",
    aliases=["Prefix"],
)
@commands.has_role(PugAdmin)
async def _prefix(ctx, new_prefix: str):
    bot.command_prefix = new_prefix
    await ctx.send(f"Command Prefix changed to: {bot.command_prefix}")




bot.run(TOKEN)
