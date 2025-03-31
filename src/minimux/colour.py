import curses


def _scale(v: int) -> int:
    return int(v * 1000 / 256)


class ColourManager:
    def __init__(self):
        self.colours = {
            "black": curses.COLOR_BLACK,
            "blue": curses.COLOR_BLUE,
            "cyan": curses.COLOR_CYAN,
            "green": curses.COLOR_GREEN,
            "magenta": curses.COLOR_MAGENTA,
            "red": curses.COLOR_RED,
            "white": curses.COLOR_WHITE,
            "yellow": curses.COLOR_YELLOW,
        }
        self.next_colour = 8
        self.colour_pairs = []

    def make_pair(self, fg: str | int | None, bg: str | int | None) -> int:
        if fg is None and bg is None:
            return 0

        # colour string to curses colour
        f = self.parse_colour(fg)
        b = self.parse_colour(bg)

        try:
            # try to find cached value
            n = self.colour_pairs.index((f, b))
        except ValueError:
            # create new colour pair and cache
            n = len(self.colour_pairs)
            curses.init_pair(n + 1, f, b)
            self.colour_pairs.append((f, b))

        return curses.color_pair(n + 1)

    def parse_colour(self, colour: str | int | None) -> int:
        # int values are already parsed
        if isinstance(colour, int):
            return colour

        # empty string or none signals default
        if not colour:
            return -1

        # check for cached colours
        if colour in self.colours:
            return self.colours[colour]

        # try to parse
        if colour.startswith("#"):
            return self.parse_hex(colour)
        elif colour.startswith("rgb("):
            return self.parse_rgb(colour)
        else:
            raise ValueError("invalid colour: " + colour)

    def parse_hex(self, hex_code: str) -> int:
        res = self.next_colour
        self.next_colour += 1
        curses.init_color(
            res,
            _scale(int(hex_code[1:3], 16)),
            _scale(int(hex_code[3:5], 16)),
            _scale(int(hex_code[5:7], 16)),
        )
        return res

    def parse_rgb(self, rgb: str) -> int:
        res = self.next_colour
        self.next_colour += 1
        r, g, b = rgb[4:-1].split(",")
        curses.init_color(
            res,
            _scale(int(r)),
            _scale(int(g)),
            _scale(int(b)),
        )
        return res
