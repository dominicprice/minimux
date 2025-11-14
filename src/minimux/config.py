import configparser
import curses
import shlex
from dataclasses import dataclass
from typing import Self, TextIO

from pyte.screens import Char

import minimux.utils as utils
from minimux.colour import ColourManager


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
        # we set the bold flag to true if the colour is bright
        bold = char.bold

        # parse fg colour - if it is a valid hex string, then prepend a
        # #. else treat it as a colour name
        fg = char.fg
        try:
            int(fg, base=16)
            fg = "#" + fg
        except ValueError:
            if fg.startswith("bright"):
                bold = True
                fg = fg[6:]

        # parse bg in the same way as fg
        bg = char.bg
        try:
            int(bg, base=16)
            bg = "#" + bg
        except ValueError:
            if bg.startswith("bright"):
                bold = True
                bg = bg[6:]

        return cls(
            fg=fg,
            bg=bg,
            blink=char.blink,
            bold=bold,
            reverse=char.reverse,
            underline=char.underscore,
            italic=char.italics,
        )

    def __or__(self, other: object) -> "Attr":
        if not isinstance(other, Attr):
            raise TypeError
        return Attr(
            fg=utils.combine(self.fg, other.fg),
            bg=utils.combine(self.bg, other.bg),
            blink=utils.combine(self.blink, other.blink),
            bold=utils.combine(self.bold, other.bold),
            dim=utils.combine(self.dim, other.dim),
            reverse=utils.combine(self.reverse, other.reverse),
            standout=utils.combine(self.standout, other.standout),
            underline=utils.combine(self.underline, other.underline),
            italic=utils.combine(self.italic, other.italic),
        )

    def __call__(self, colour_manager: ColourManager):
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


@dataclass
class Element:
    name: str
    attr: Attr
    weight: int


@dataclass
class Command(Element):
    command: list[str]
    title: str | None
    shell: bool
    input: str | None
    padding: tuple[int, int, int, int]
    title_attr: Attr
    no_close_stdin: bool
    charset: str


@dataclass
class Panel(Element):
    vertical: bool
    children: list[Element]


class MiniMuxConfigParser(configparser.ConfigParser):
    def __init__(self):
        super().__init__(
            delimiters=["="],
            comment_prefixes=["#"],
            default_section="default",
        )

    def create_panels(
        self,
        section: "configparser.SectionProxy",
        prefix: str,
        default_attr: Attr,
    ) -> Element:
        if "command" in section:
            return self.parse_command(section, prefix, default_attr)
        elif "panels" in section:
            return self.parse_panel(section, prefix, default_attr)
        else:
            raise ValueError("command or panels must be specified")

    def parse_command(
        self,
        section: "configparser.SectionProxy",
        prefix: str,
        default_attr: Attr,
    ) -> Command:
        title = section.get("title", None)
        command = section["command"]
        attr = default_attr | self.parse_attrs(section)
        title_attr = attr
        if s := section.get("title_attr", None):
            title_attr = attr | self.parse_attrs(self[s])
        weight = section.getint("weight", 1)
        shell = section.getboolean("shell", False)
        input = section.get("input", None)
        padding = self.aspadding(section.get("padding", None))
        no_close_stdin = section.getboolean("no_close_stdin", False)
        charset = section.get("charset", "utf-8")

        return Command(
            prefix + ":" + section.name,
            attr,
            weight,
            shlex.split(command),
            title,
            shell,
            input,
            padding,
            title_attr,
            no_close_stdin,
            charset,
        )

    def parse_panel(
        self,
        section: "configparser.SectionProxy",
        prefix: str,
        default_attr: Attr,
    ) -> Panel:
        prefix += ":" + section.name
        vertical = section.getboolean("vertical", False)
        attr = default_attr | self.parse_attrs(section)
        children: list[Element] = []
        weight = section.getint("weight", 1)
        for subsection in self.aslist(section["panels"]):
            child = self.create_panels(self[subsection], prefix, attr)
            children.append(child)

        return Panel(prefix, attr, weight, vertical, children)

    def parse_attrs(self, section: "configparser.SectionProxy") -> Attr:
        attr = Attr()
        attr.fg = section.get("fg", None)
        attr.bg = section.get("bg", None)
        attr.blink = section.getboolean("blink", None)
        attr.bold = section.getboolean("bold", None)
        attr.dim = section.getboolean("dim", None)
        attr.reverse = section.getboolean("reverse", None)
        attr.standout = section.getboolean("standout", None)
        attr.underline = section.getboolean("underline", None)
        attr.italic = section.getboolean("italic", None)
        return attr

    def aslist(self, value: str):
        return [v.strip() for v in value.split(",") if v.strip()]

    def aspadding(self, value: str | None) -> tuple[int, int, int, int]:
        if value is None:
            return (0, 0, 0, 0)
        ps = [int(v) for v in value.split(",")]
        if len(ps) == 1:
            return (ps[0], ps[0], ps[0], ps[0])
        elif len(ps) == 2:
            return (ps[1], ps[0], ps[1], ps[0])
        elif len(ps) == 4:
            return (ps[0], ps[1], ps[2], ps[3])
        raise ValueError("expected p or px,py or pt,pr,pb,pl")


@dataclass
class Config:
    title: str | None
    content: Element
    sep_attr: Attr
    title_attr: Attr

    @classmethod
    def from_parser(cls, parser: MiniMuxConfigParser) -> "Config":
        main = parser["main"]
        title = main.pop("title", None)
        content = parser.create_panels(main, "", Attr())
        base_attr = parser.parse_attrs(main)
        sep_attrs = base_attr
        if "seperator" in parser:
            sep_attrs = base_attr | parser.parse_attrs(parser["seperator"])
        title_attrs = base_attr
        if "title" in parser:
            title_attrs = base_attr | parser.parse_attrs(parser["title"])

        return cls(title, content, sep_attrs, title_attrs)

    @classmethod
    def from_file(cls, f: TextIO) -> "Config":
        parser = MiniMuxConfigParser()
        parser.read_file(f)
        return cls.from_parser(parser)
