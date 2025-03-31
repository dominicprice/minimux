from minimux.colour import ColourManager
import unittest.mock


@unittest.mock.patch("curses.init_color", lambda *args, **kwargs: 0)
@unittest.mock.patch("curses.init_pair", lambda *args, **kwargs: 0)
@unittest.mock.patch("curses.color_pair", lambda *args, **kwargs: 0)
def test_colour():
    cm = ColourManager()
    cm.make_pair(None, None)
    cm.make_pair("rgb(100, 20, 12)", "#aadb2d")
    cm.parse_hex("#ffffff")
    cm.parse_rgb("rgb(100, 240, 128)")
