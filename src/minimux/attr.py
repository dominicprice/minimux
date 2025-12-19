import curses
from dataclasses import dataclass, field
from typing import Self

from pyte.screens import Char

from minimux.colour import Colour, ColourManager, DefaultColour
from minimux.utils import combine


@dataclass
class Attr:
    fg: Colour = field(default_factory=lambda: DefaultColour())
    bg: Colour = field(default_factory=lambda: DefaultColour())
    blink: bool | None = None
    bold: bool | None = None
    dim: bool | None = None
    reverse: bool | None = None
    standout: bool | None = None
    underline: bool | None = None
    italic: bool | None = None

    @classmethod
    def from_char(cls, char: Char) -> Self:
        "Get the curses attribute of a Char from the pty"

        return cls(
            fg=Colour.new(char.fg),
            bg=Colour.new(char.bg),
            blink=char.blink or None,
            bold=char.bold or None,
            reverse=char.reverse or None,
            underline=char.underscore or None,
            italic=char.italics or None,
        )

    def __or__(self, other: object) -> "Attr":
        """
        Combine two attributes, with any values set in other
        overriding the values in self
        """
        if not isinstance(other, Attr):
            raise TypeError

        return Attr(
            fg=self.fg if other.fg == DefaultColour() else other.fg,
            bg=self.bg if other.bg == DefaultColour() else other.bg,
            blink=combine(self.blink, other.blink),
            bold=combine(self.bold, other.bold),
            dim=combine(self.dim, other.dim),
            reverse=combine(self.reverse, other.reverse),
            standout=combine(self.standout, other.standout),
            underline=combine(self.underline, other.underline),
            italic=combine(self.italic, other.italic),
        )

    def __call__(self, colour_manager: ColourManager | None = None) -> int:
        """
        Convert the attribute into a curses attribute value
        """
        attr = 0
        if colour_manager is not None:
            pair = colour_manager.make_pair(self.fg, self.bg)
            attr = curses.color_pair(pair)
        if self.blink:
            attr |= curses.A_BLINK
        if self.bold:
            attr |= curses.A_BOLD
        if self.dim:
            attr |= curses.A_DIM
        if self.reverse:
            attr |= curses.A_REVERSE
        if self.standout:
            attr |= curses.A_STANDOUT
        if self.underline:
            attr |= curses.A_UNDERLINE
        if self.italic:
            attr |= curses.A_ITALIC
        return attr
