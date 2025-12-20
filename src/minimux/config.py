import configparser
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

import minimux.utils as utils
from minimux.attr import Attr
from minimux.colour import Colour, DefaultColour
from minimux.padding import Padding


@dataclass
class Config:
    title: str | None
    content: "Config.Element"
    sep_attr: Attr
    title_attr: Attr

    @dataclass
    class Element:
        name: str
        attr: Attr
        weight: int

    @dataclass
    class Command(Element):
        command: list[str]
        title: str | None
        input: str | None
        padding: Padding
        title_attr: Attr
        no_close_stdin: bool
        charset: str
        cwd: Path
        watch: int
        tabsize: int

    @dataclass
    class Panel(Element):
        vertical: bool
        children: "list[Config.Element]"

    @classmethod
    def from_parser(cls, parser: "MiniMuxConfigParser") -> "Config":
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
    def from_file(cls, f: TextIO, cwd: Path) -> "Config":
        parser = MiniMuxConfigParser(cwd)
        parser.read_file(f)
        return cls.from_parser(parser)


class MiniMuxConfigParser(configparser.ConfigParser):
    def __init__(self, cwd: Path):
        super().__init__(
            delimiters=["="],
            comment_prefixes=["#"],
            default_section="default",
            converters={
                "list": utils.split_list,
                "path": Path,
                "colour": Colour.new,
            },
        )
        self.cwd = cwd

    def create_panels(
        self,
        section: "configparser.SectionProxy",
        prefix: str,
        default_attr: Attr,
    ) -> Config.Element:
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
    ) -> Config.Command:
        title = section.get("title", None)
        shell = section.getboolean("shell", False)
        if shell:
            command = ["sh", "-c", section["command"]]
        else:
            command = shlex.split(section["command"])
        attr = default_attr | self.parse_attrs(section)
        title_attr = attr
        if s := section.get("title_attr", None):
            title_attr = attr | self.parse_attrs(self[s])
        weight = section.getint("weight", 1)
        input = section.get("input", None)
        padding = Padding.parse(section.get("padding", "0"))
        no_close_stdin = section.getboolean("no_close_stdin", False)
        charset = section.get("charset", "utf-8")
        cwd: Path = section.getpath("cwd", self.cwd)
        watch = section.getint("watch", 0)
        tabsize = section.getint("tabsize", 4)

        return Config.Command(
            prefix + ":" + section.name,
            attr,
            weight,
            command,
            title,
            input,
            padding,
            title_attr,
            no_close_stdin,
            charset,
            cwd,
            watch,
            tabsize,
        )

    def parse_panel(
        self,
        section: "configparser.SectionProxy",
        prefix: str,
        default_attr: Attr,
    ) -> Config.Panel:
        prefix += ":" + section.name
        vertical = section.getboolean("vertical", False)
        attr = default_attr | self.parse_attrs(section)
        children: list[Config.Element] = []
        weight = section.getint("weight", 1)
        for i, subsection in enumerate(section.getlist("panels", [])):
            child = self.create_panels(
                self[subsection],
                f"{prefix}.{i}",
                attr,
            )
            children.append(child)

        return Config.Panel(prefix, attr, weight, vertical, children)

    def parse_attrs(self, section: "configparser.SectionProxy") -> Attr:
        attr = Attr()
        attr.fg = section.getcolour("fg", DefaultColour())
        attr.bg = section.getcolour("bg", DefaultColour())
        attr.blink = section.getboolean("blink", None)
        attr.bold = section.getboolean("bold", None)
        attr.dim = section.getboolean("dim", None)
        attr.reverse = section.getboolean("reverse", None)
        attr.standout = section.getboolean("standout", None)
        attr.underline = section.getboolean("underline", None)
        attr.italic = section.getboolean("italic", None)
        return attr
