import curses
from dataclasses import dataclass
import re
from typing import Self

re_hexcolour = re.compile(r"#([A-Fa-f0-9]{1,2})([A-Fa-f0-9]{1,2})([A-Fa-f0-9]{1,2})")
re_rgbcolour = re.compile(r"rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)")


@dataclass(frozen=True)
class Colour:
    @staticmethod
    def new(spec: str) -> "Colour":
        if m := re_hexcolour.fullmatch(spec):
            return RGBColour.from_rgb(
                int(m[1], 16),
                int(m[2], 16),
                int(m[3], 16),
            )
        elif m := re_rgbcolour.fullmatch(spec):
            return RGBColour.from_rgb(
                int(m[1]),
                int(m[2]),
                int(m[3]),
            )
        return NamedColour(spec)


@dataclass(frozen=True)
class NamedColour(Colour):
    name: str


@dataclass(frozen=True)
class RGBColour(Colour):
    r: int
    g: int
    b: int

    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> Self:
        return cls(r * 1000 // 256, g * 1000 // 256, b * 1000 // 256)


@dataclass
class ColourPair:
    fg: Colour
    bg: Colour


class ColourManager:
    def __init__(self):
        self.colours: dict[Colour, int] = {}
        self.next_colour = 8
        self.colour_pairs = []

        # inbuilt curses colours
        self.colours[NamedColour("black")] = curses.COLOR_BLACK
        self.colours[NamedColour("blue")] = curses.COLOR_BLUE
        self.colours[NamedColour("cyan")] = curses.COLOR_CYAN
        self.colours[NamedColour("green")] = curses.COLOR_GREEN
        self.colours[NamedColour("magenta")] = curses.COLOR_MAGENTA
        self.colours[NamedColour("red")] = curses.COLOR_RED
        self.colours[NamedColour("white")] = curses.COLOR_WHITE
        self.colours[NamedColour("yellow")] = curses.COLOR_YELLOW

        # terminal "bright" colours
        self.add_named_colour("brightblack", 85, 87, 83)
        self.add_named_colour("brightblue", 124, 158, 203)
        self.add_named_colour("brightcyan", 112, 223, 224)
        self.add_named_colour("brightgreen", 158, 224, 85)
        self.add_named_colour("brightmagenta", 166, 129, 165)
        self.add_named_colour("brightred", 220, 63, 54)
        self.add_named_colour("brightwhite", 238, 238, 236)
        self.add_named_colour("brightyellow", 249, 234, 107)

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

    def parse_colour(self, spec: str | int | None) -> int:
        # int values are already parsed
        if isinstance(spec, int):
            return spec

        # empty string or none signals default
        if not spec:
            return -1

        # create colour from spec and attempt to get from cache
        colour = Colour.new(spec)
        if colour in self.colours:
            return self.colours[colour]

        # create a new colour if it is an rgb definition
        if isinstance(colour, RGBColour):
            return self.add_colour(colour)

        # invalid color, return default
        return -1

    def add_colour(self, colour: RGBColour) -> int:
        res = self.get_next_colour_index()
        curses.init_color(res, colour.r, colour.g, colour.b)
        self.colours[colour] = res
        return res

    def add_named_colour(self, name: str, r: int, g: int, b: int) -> int:
        res = self.get_next_colour_index()
        colour = RGBColour.from_rgb(r, g, b)
        curses.init_color(res, colour.r, colour.g, colour.b)
        self.colours[NamedColour(name)] = res
        return res

    def get_next_colour_index(self) -> int:
        res = self.next_colour
        self.next_colour += 1
        return res
