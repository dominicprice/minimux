import curses
from dataclasses import dataclass
from typing import Self
from minimux.colour import ColourManager
from minimux.utils import combine

from pyte.screens import Char


@dataclass
class Attr:
    fg: str | int | None = None
    bg: str | int | None = None
    blink: bool | None = None
    bold: bool | None = None
    dim: bool | None = None
    reverse: bool | None = None
    standout: bool | None = None
    underline: bool | None = None
    italic: bool | None = None

    @classmethod
    def from_char(cls, char: Char) -> Self:
        # parse fg colour - if it is a valid hex string, then prepend a
        # #. else treat it as a colour name
        fg = None
        if char.fg != "default":
            try:
                int(char.fg, base=16)
                fg = "#" + char.fg
            except ValueError:
                fg = char.fg

        # parse bg in the same way as fg
        bg = None
        if char.bg != "default":
            try:
                int(char.bg, base=16)
                bg = "#" + char.bg
            except ValueError:
                bg = char.bg

        return cls(
            fg=fg,
            bg=bg,
            blink=char.blink or None,
            bold=char.bold or None,
            reverse=char.reverse or None,
            underline=char.underscore or None,
            italic=char.italics or None,
        )

    def __or__(self, other: object) -> "Attr":
        if not isinstance(other, Attr):
            raise TypeError
        return Attr(
            fg=combine(self.fg, other.fg),
            bg=combine(self.bg, other.bg),
            blink=combine(self.blink, other.blink),
            bold=combine(self.bold, other.bold),
            dim=combine(self.dim, other.dim),
            reverse=combine(self.reverse, other.reverse),
            standout=combine(self.standout, other.standout),
            underline=combine(self.underline, other.underline),
            italic=combine(self.italic, other.italic),
        )

    def __call__(self, colour_manager: ColourManager | None = None):
        attr = 0
        if colour_manager is not None:
            attr = colour_manager.make_pair(self.fg, self.bg)
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
