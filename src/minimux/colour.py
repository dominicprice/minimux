import curses
import re
from dataclasses import dataclass
from typing import Self

from minimux.utils import Counter, UniqueDict

re_hexcolour = re.compile(r"#?([A-Fa-f0-9]{1,2})([A-Fa-f0-9]{1,2})([A-Fa-f0-9]{1,2})")
re_rgbcolour = re.compile(r"rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)")


@dataclass(frozen=True)
class Colour:
    @staticmethod
    def new(spec: str) -> "Colour":
        if spec == "default":
            return DefaultColour()
        elif m := re_hexcolour.fullmatch(spec):
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


@dataclass(frozen=True)
class DefaultColour(Colour):
    pass


@dataclass(frozen=True)
class ColourPair:
    fg: Colour
    bg: Colour


class ColourManager:
    def __init__(self):
        self.colours: UniqueDict[Colour, int] = UniqueDict()
        self.next_colour = Counter(8, curses.COLORS)
        self.colour_pairs: UniqueDict[ColourPair, int] = UniqueDict()
        self.next_colour_pair = Counter(1, curses.COLOR_PAIRS)

        # default colour
        self.colours[DefaultColour()] = -1

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
        self._init("brightblack", 85, 87, 83)
        self._init("brightblue", 124, 158, 203)
        self._init("brightcyan", 112, 223, 224)
        self._init("brightgreen", 158, 224, 85)
        self._init("brightmagenta", 166, 129, 165)
        self._init("brightred", 220, 63, 54)
        self._init("brightwhite", 238, 238, 236)
        self._init("brightyellow", 249, 234, 107)

        # ensure we don't overwrite the named colours
        self.next_colour.clamp()

    def make_pair(self, fg: Colour, bg: Colour) -> int:
        "Returns a curses colour pair id for the given colours"
        pair = ColourPair(fg, bg)

        if pair in self.colour_pairs:
            return self.colour_pairs[pair]

        res = self.next_colour_pair()
        curses.init_pair(res, self.make_colour(fg), self.make_colour(bg))
        self.colour_pairs[pair] = res
        return res

    def make_colour(self, colour: Colour) -> int:
        "Returns a curses colour id for the given colour"
        if colour in self.colours:
            return self.colours[colour]

        # create a new colour if it is an rgb definition
        if isinstance(colour, RGBColour):
            res = self.next_colour()
            curses.init_color(res, colour.r, colour.g, colour.b)
            self.colours[colour] = res
            return res

        # invalid color, return default
        return -1

    def _init(self, name: str, r: int, g: int, b: int) -> int:
        res = self.next_colour()
        colour = RGBColour.from_rgb(r, g, b)
        curses.init_color(res, colour.r, colour.g, colour.b)
        self.colours[NamedColour(name)] = res
        return res
