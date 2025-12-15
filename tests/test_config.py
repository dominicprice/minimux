from io import StringIO

from pathlib import Path

from minimux.config import Config


def test_config():
    ini = """
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
    """

    StringIO(ini)
    config = Config.from_file(StringIO(ini), Path("."))

    assert config.title == "Example Minimux"
    content = config.content
    assert isinstance(content, Config.Panel)
    assert content.vertical == False
    assert len(content.children) == 2

    frontend = content.children[0]
    assert isinstance(frontend, Config.Command)
    assert frontend.title == "Frontend"
    assert frontend.command == ["make", "-C", "frontend", "dev"]

    backend = content.children[1]
    assert isinstance(backend, Config.Panel)
    assert backend.vertical == True
    assert len(backend.children) == 2

    db = backend.children[0]
    assert isinstance(db, Config.Command)
    assert db.title == "Database"
    assert db.command == ["make", "-C", "db", "dev"]

    api = backend.children[1]
    assert isinstance(api, Config.Command)
    assert api.title == "API"
    assert api.command == ["make", "-C", "api", "dev"]
