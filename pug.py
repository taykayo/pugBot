class Team:
    def __init__(self, pug_size, Color):
        # Initialize Team Data
        self.color = Color
        self.name = Color + "Team"
        if self.color == "Blue":
            self.pick_id = 1
        else:
            self.pick_id = 2
        self.mids = []
        self.keeps = []
        self.defs = []

        if pug_size == 3:
            self.keep_limit = 1
            self.def_limit = 0
            self.mid_limit = 2
        if pug_size == 5:
            self.keep_limit = 1
            self.def_limit = 1
            self.mid_limit = 3


class Pug:

    def __init__(self, pug_size):
        # Initialize pug data based on game size (3v3/5v5)

        self.player_limit = pug_size * 2
        self.player_count = 0
        self.keep_limit = 2
        self.state = 0  # 0 = Queuing, 1 = Picking
        self.mids = []
        self.keeps = []
        self.defs = []
        self.pug_size = pug_size
        self.pick_order_str = "Normal"

        if pug_size == 3:
            self.pick_order = [1, 2, 1, 2]
            self.mid_limit = 4
            self.def_limit = 0

        if pug_size == 5:
            self.pick_order = [1, 2, 2, 1, 2, 1]  # standard for NA, this is blitz. alternate is just alternating picks
            self.mid_limit = 6
            self.def_limit = 2

    def pug_status(self, arg):
        ret = ''
        if self.state == 0:
            ret += f"**\|\| Signing up ({self.player_count}/{self.player_limit}): \|\|** \n"
            if arg:
                ret += arg + "\n"
            ret += f"**Keepers** [{len(self.keeps)}/{self.keep_limit}] \n"
            if self.pug_size == 5:
                ret += f"**Defenders** [{len(self.defs)}/{self.def_limit}] \n"

            ret += f"**Midfielders** [{len(self.mids)}/{self.mid_limit}] \n\n"
            if self.pug_size == 5:
                ret += f"**Pug Type**: Normal 5v5 \n"
            else:
                ret += f"**Pug Type**: Normal 3v3 \n"

            ret += f"**Pick Order**: Normal \n"

        return ret

