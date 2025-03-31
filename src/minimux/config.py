import curses
import configparser
import re
import shlex
from typing import TextIO
from dataclasses import dataclass, field

from minimux.colour import ColourManager
from minimux.rules import LiteralRule, RegexRule, Rule
import minimux.utils as utils


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
        return attr


@dataclass
class Element:
    attr: Attr
    weight: int


@dataclass
class Command(Element):
    command: list[str]
    title: str | None
    rules: dict[Rule, Attr]


@dataclass
class Panel(Element):
    split_vertically: bool
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
        default_attr: Attr,
    ) -> Element:
        if "command" in section:
            return self.parse_command(section, default_attr)
        elif "panels" in section:
            return self.parse_panel(section, default_attr)
        else:
            raise ValueError("command or panels must be specified")

    def parse_command(
        self,
        section: "configparser.SectionProxy",
        default_attr: Attr,
    ) -> Command:
        title = section.get("title", None)
        command = section["command"]
        attr = default_attr | self.parse_attrs(section)
        rules = self.parse_rules(self.aslist(section.get("rules", "")), attr)
        weight = section.getint("weight", 1)

        return Command(attr, weight, shlex.split(command), title, rules)

    def parse_panel(
        self,
        section: "configparser.SectionProxy",
        default_attr: Attr,
    ) -> Panel:
        vertical = section.getboolean("vertical", False)
        attr = default_attr | self.parse_attrs(section)
        children: list[Element] = []
        weight = section.getint("weight", 1)
        for subsection in self.aslist(section["panels"]):
            child = self.create_panels(self[subsection], attr)
            children.append(child)

        return Panel(attr, weight, vertical, children)

    def parse_rules(
        self, rule_names: list[str], default_attr: Attr
    ) -> dict[Rule, Attr]:
        rules: dict[Rule, Attr] = {}
        for rule_name in rule_names:
            rule, attr = self.parse_rule(rule_name, default_attr)
            rules[rule] = attr
        return rules

    def parse_rule(self, rule_name: str, default_attr: Attr) -> tuple[Rule, Attr]:
        rule = self[rule_name]
        if "regex" in rule:
            return self.parse_regex_rule(rule, default_attr)
        elif "literal" in rule:
            return self.parse_literal_rule(rule, default_attr)
        else:
            raise ValueError("invalid rule: must contain 'regex' or 'literal' option")

    def parse_regex_rule(
        self,
        section: "configparser.SectionProxy",
        default_attr: Attr,
    ) -> tuple[Rule, Attr]:
        pattern = section["regex"]
        flags = re.NOFLAG
        if section.getboolean("ascii", False):
            flags |= re.ASCII
        if section.getboolean("ignorecase", False):
            flags |= re.IGNORECASE
        if section.getboolean("locale", False):
            flags |= re.LOCALE
        if section.getboolean("multiline", False):
            flags |= re.MULTILINE
        if section.getboolean("dotall", False):
            flags |= re.DOTALL
        if section.getboolean("verbose", False):
            flags |= re.VERBOSE

        rule = RegexRule(pattern, flags)
        attr = default_attr | self.parse_attrs(section)
        return rule, attr

    def parse_literal_rule(
        self,
        section: "configparser.SectionProxy",
        default_attr: Attr,
    ) -> tuple[Rule, Attr]:
        pattern = section["literal"]
        ignorecase = section.getboolean("ignorecase", False)

        rule = LiteralRule(pattern, ignorecase)
        attr = default_attr | self.parse_attrs(section)
        return rule, attr

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
        return attr

    def aslist(self, value: str):
        return [v.strip() for v in value.split(",") if v.strip()]


@dataclass
class Config:
    title: str | None = None
    content: Element = field(default_factory=lambda: Element(Attr(), 1))
    sep_attr: Attr = field(default_factory=Attr)
    title_attr: Attr = field(default_factory=Attr)

    @classmethod
    def from_parser(cls, parser: MiniMuxConfigParser) -> "Config":
        main = parser["main"]
        title = main.pop("title", None)
        content = parser.create_panels(main, Attr())
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
