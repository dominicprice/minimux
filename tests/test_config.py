from io import StringIO
import curses
import re

from minimux.config import Config, Panel, Command
from minimux.colour import ColourManager
from minimux.rules import LiteralRule, RegexRule


class MockColourManager(ColourManager):
    def make_pair(self, fg, bg):
        return 1

    def parse_colour(self, colour):
        return 1


def test_config():
    ini = """
        [default]
        rules = errorrule

        [seperator]
        fg = #ddddff

        [title]
        bold = on

        [main]
        title = Example Minimux
        panels = frontend,backend

        [frontend]
        title = Frontend
        command = make -C frontend dev

        [backend]
        vertical = true
        panels = db,api

        [db]
        title = Database
        command = make -C db dev

        [api]
        title = API
        command = make -C api dev
        rules=errorrule,warnrule

        [errorrule]
        regex = error
        ascii = on
        fg = #5a4a3a
        bold = on
        underline = on

        [warnrule]
        literal = warn
        ignorecase = true
    """

    cm = MockColourManager()

    StringIO(ini)
    config = Config.from_file(StringIO(ini), cm)

    error_rule = RegexRule("error", re.ASCII)
    error_attr = curses.A_BOLD | curses.A_UNDERLINE | 1

    warn_rule = LiteralRule("warn", True)
    warn_attr = 0

    assert config.title == "Example Minimux"
    content = config.content
    assert isinstance(content, Panel)
    assert content.split_vertically == False
    assert len(content.children) == 2

    frontend = content.children[0]
    assert isinstance(frontend, Command)
    assert frontend.title == "Frontend"
    assert frontend.command == ["make", "-C", "frontend", "dev"]
    assert len(frontend.rules) == 1
    assert frontend.rules[error_rule] == error_attr

    backend = content.children[1]
    assert isinstance(backend, Panel)
    assert backend.split_vertically == True
    assert len(backend.children) == 2

    db = backend.children[0]
    assert isinstance(db, Command)
    assert db.title == "Database"
    assert db.command == ["make", "-C", "db", "dev"]
    assert len(db.rules) == 1
    assert db.rules[error_rule] == error_attr

    api = backend.children[1]
    assert isinstance(api, Command)
    assert api.title == "API"
    assert api.command == ["make", "-C", "api", "dev"]
    assert len(api.rules) == 2
    assert api.rules[error_rule] == error_attr
    assert api.rules[warn_rule] == warn_attr
