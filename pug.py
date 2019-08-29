import configparser

blue_team = None
red_team = None


class Team:
    def __init__(self):
        # Initialize Team Data
        self.mids = []
        self.keep = []
        self.defs = []
        self.player_count = 0

    def add_player(self, position, user):
        if position == "mid":
            self.mids.append(user)
        elif position == "keep":
            self.keep.append(user)
        elif position == "defs":
            self.defs.append(user)

    def team_string(self):
        team = []
        if self.keep:
            team.append(f"(K) {self.keep[0].name}")
        if self.defs:
            team.append(f"(D) {self.defs[0].name}")
        if self.mids:
            mid_string = ", ".join(f"(M) {x.name}" for x in self.mids)
            team.append(mid_string)
        return ", ".join(team)


class PugTeam(Team):
    def __init__(self, pug_size, color):
        super().__init__()
        self.color = color
        self.name = color + "Team"
        if self.color == "Blue":
            self.pick_id = 1
        else:
            self.pick_id = 2
        self.captain = None
        if pug_size == 3:
            self.keep_limit = 1
            self.defs_limit = 0
            self.mid_limit = 2
            self.player_limit = 3
        if pug_size == 5:
            self.keep_limit = 1
            self.defs_limit = 1
            self.mid_limit = 3
            self.player_limit = 5

class ScrimTeam(Team):
    def __init__(self):
        super().__init__()
        self.color = "Blue"
        self.name = ""
        self.pug_size = 5
        self.keep_limit = 1
        self.defs_limit = 1
        self.mid_limit = 3
        self.player_limit = 5


class Game:
    def __init__(self):
        self.player_count = 0
        self.state = 0
        self.mids = []
        self.keep = []
        self.defs = []

    def check_player_count(self):
        pass

    def add_player(self, user, position):
        if position == "mid":
            self.mids.append(user)
        elif position == "keep":
            self.keep.append(user)
        elif position == "defs":
            self.defs.append(user)
        self.player_count = len(self.mids) + len(self.keep) + len(self.defs)

    def remove_player(self, user):
        if user in self.mids:
            self.mids.remove(user)
        elif user in self.keep:
            self.keep.remove(user)
        elif user in self.defs:
            self.defs.remove(user)
        self.player_count = len(self.mids) + len(self.keep) + len(self.defs)


class Pug(Game):
    captains = None
    pick_order_str = "Normal"
    next_pick = 0

    def __init__(self, pug_size):
        super().__init__()
        # Initialize pug data based on game size (3v3/5v5)
        self.pug_size = pug_size
        self.player_limit = pug_size * 2
        if pug_size == 3:
            self.pick_order = [1, 2, 2, 1]
            self.mid_limit = 4
            self.def_limit = 0
            self.keep_limit = 2
        if pug_size == 5:
            # standard for NA, alternate is blitz
            self.pick_order = [1, 2, 2, 1, 2, 1, 2]
            self.mid_limit = 6
            self.def_limit = 2
            self.keep_limit = 2

    def check_player_count(self):
        if self.player_limit == self.player_count:
            self.state = 1
            return 1
        else:
            return 0


    def pug_status(self, arg, *args):
        def get_names(users):
            return ", ".join(user.name for user in users)

        ret = ""
        if self.state == 0:
            if self.captains == "d":
                pug_captains = "Defenders"
            elif self.captains == "k":
                pug_captains = "Keepers"
            else:
                pug_captains = "Random"
            ret += f"**\\|\\| Signing up ({self.player_count}/{self.player_limit}): \\|\\|** \n"
            ret += arg + "\n"
            ret += f"**Keepers** [{len(self.keep)}/{self.keep_limit}] {str(get_names(self.keep))} \n"
            if self.pug_size == 5:
                ret += f"**Defenders** [{len(self.defs)}/{self.def_limit}] {str(get_names(self.defs))} \n"

            ret += f"**Midfielders** [{len(self.mids)}/{self.mid_limit}] {str(get_names(self.mids))} \n\n"
            if self.pug_size == 5:
                ret += f"**Pug Type**: Normal 5v5 \n"
                ret += f"**Captains**: {pug_captains}\n"
            else:
                ret += f"**Pug Type**: Normal 3v3 \n"

            ret += f"**Pick Order**: {self.pick_order_str} \n"
        elif self.state == 1:
            # TODO: blue_team and red_team should either be declared as global (if that's the intent) or renamed
            blue_team = args[0]
            red_team = args[1]

            po_string_arr = ["B" if x == 1 else "R" for x in self.pick_order]

            po_string_arr[self.next_pick] = "[" + po_string_arr[self.next_pick] + "]"
            po_string = " - ".join(map(str, po_string_arr)) if len(po_string_arr) is not 0 else ""

            ret += f"**\\|\\| Picking Teams: \\|\\|** \n"
            ret += arg + "\n"
            if len(self.keep) > 0:
                ret += f"**Keepers** [{len(self.keep)}] {str(get_names(self.keep))} \n"
            if len(self.defs) > 0:
                ret += f"**Defenders** [{len(self.defs)}] {str(get_names(self.defs))} \n"
            if len(self.mids) > 0:
                ret += f"**Midfielders** [{len(self.mids)}] {str(get_names(self.mids))} \n\n"
            ret += f"**Blue Team** - Captain {blue_team.captain.name} \n {blue_team.team_string()} \n\n"
            ret += f"**Red Team** - Captain {red_team.captain.name} \n {red_team.team_string()} \n\n"
            ret += f"**Pick Order Progress**: {po_string}  \n"
            if self.pick_order[self.next_pick] == 1:
                ret += f"**BLUE TEAM** (<@{blue_team.captain.id}>), Please pick a player."
            elif self.pick_order[self.next_pick] == 2:
                ret += f"**RED TEAM** (<@{red_team.captain.id}>), Please pick a player."
        elif self.state == 2:
            # TODO: blue_team and red_team should either be declared as global (if that's the intent) or renamed
            blue_team = args[0]
            red_team = args[1]
            ret += f"**\\|\\| Match is starting, have fun! \\|\\|** \n"
            ret += f"**Blue Team** - Captain {blue_team.captain.name} \n {blue_team.team_string()} \n\n"
            ret += f"**Red Team** - Captain {red_team.captain.name} \n {red_team.team_string()} \n\n "
        return ret

    def team_pick(self, team, user, *auto):
        if not auto:
            self.next_pick += 1

        if user in self.mids:
            team.add_player("mid", user)
            self.mids.remove(user)
        elif user in self.keep:
            team.add_player("keep", user)
            self.keep.remove(user)
        elif user in self.defs:
            team.add_player("defs", user)
            self.defs.remove(user)

        self.player_count = len(self.mids) + len(self.keep) + len(self.defs)
        if self.player_count == 0:
            self.state = 2

    def spo(self, pick_order):
        if pick_order.lower() == "blitz":
            self.pick_order = [1, 2, 2, 1, 1, 2, 1]
            self.pick_order_str = "Blitz"
        elif pick_order.lower() == "normal":
            self.pick_order = [1, 2, 2, 1, 2, 1, 2]
            self.pick_order_str = "Normal"
        elif pick_order.lower() == "linear":
            self.pick_order = [1, 2, 1, 2, 1, 2, 1]
            self.pick_order_str = "Linear"

    def set_captains(self, captains):
        self.captains = captains


class ScrimTeamReg(Game):
    def __init__(self):
        super().__init__()
        self.player_limit = 5
        self.keep_limit = 1
        self.mid_limit = 3
        self.def_limit = 1

    def pug_status(self, arg, *args):
        def get_names(users):
            return ", ".join(user.name for user in users)

        ret = ""

        ret += f"**\\|\\| Scrim Team Creation ({self.player_count}/{self.player_limit}): \\|\\|** \n"
        ret += arg + "\n"
        ret += f"**Keepers** [{len(self.keep)}/{self.keep_limit}] {str(get_names(self.keep))} \n"
        ret += f"**Defenders** [{len(self.defs)}/{self.def_limit}] {str(get_names(self.defs))} \n"
        ret += f"**Midfielders** [{len(self.mids)}/{self.mid_limit}] {str(get_names(self.mids))} \n\n"

        if self.state == 1:
            ret += f"Team is full, used !save [teamname] to save your team! \n\n"
        return ret

    def check_player_count(self):
        if self.player_limit == self.player_count:
            self.state = 1
            return 0
        elif self.player_limit > self.player_count:
            self.state = 0
            return 0


    def save(self, team_name):

        #RETURN CODE: 0 fail, 1 success, 2 Teamname already exists
        try:
            config = configparser.ConfigParser()
            config.optionxform = str
            config.read("config.ini")
            print(config)
            if team_name in config:
                return 2
            else:
                config[f"{team_name}"] = {
                    self.mids[0]: "mid",
                    self.mids[1]: "mid",
                    self.mids[2]: "mid",
                    self.defs[0]: "defs",
                    self.keep[0]: "keep"
                }
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
            return 1
        except:
            return 0


class Scrim(Game):

    def __init__(self, team):
        super().__init__()
        # Initialize pug data
        self.pug_size = 5
        self.player_limit = 5
        self.mid_limit = 3
        self.def_limit = 1
        self.keep_limit = 1
        self.team = team

    def check_player_count(self):
        if self.player_limit == self.player_count:
            self.state = 1
            return 2
        else:
            return 0

    def pug_status(self, arg, *args):
        def get_names(users):
            return ", ".join(user.name for user in users)

        ret = ""
        if self.state == 0:

            ret += f"**\\|\\| Signing up ({self.player_count}/{self.player_limit}): \\|\\|** \n"
            ret += f"**Scrim VS {self.team.name}** {self.team.team_string()} \n \n"
            ret += arg + "\n"
            ret += f"**Keepers** [{len(self.keep)}/{self.keep_limit}] {str(get_names(self.keep))} \n"
            if self.pug_size == 5:
                ret += f"**Defenders** [{len(self.defs)}/{self.def_limit}] {str(get_names(self.defs))} \n"

            ret += f"**Midfielders** [{len(self.mids)}/{self.mid_limit}] {str(get_names(self.mids))} \n\n"


        elif self.state == 1:
            # TODO: blue_team and red_team should either be declared as global (if that's the intent) or renamed
            ret += f"**\\|\\| Match is starting, have fun! \\|\\|** \n"
            ret += f"**{self.team.name}** - {self.team.team_string()} \n\n"
            ret += f"**Challengers** - {arg.team_string()} \n\n"
        return ret


