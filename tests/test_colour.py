import curses
from minimux.colour import ColourManager, DefaultColour, NamedColour, RGBColour
import unittest.mock

curses.COLORS = 17
curses.COLOR_PAIRS = 3


@unittest.mock.patch("curses.init_color", lambda *_: None)
@unittest.mock.patch("curses.init_pair", lambda *_: None)
def test_colour():
    cm = ColourManager()

    # default colour
    assert cm.make_colour(DefaultColour()) == -1

    # inbuilt colours
    assert cm.make_colour(NamedColour("green")) == 2
    assert cm.make_colour(NamedColour("red")) == 1

    # custom colours
    assert cm.make_colour(RGBColour.from_rgb(12, 13, 14)) == 16
    assert cm.make_colour(RGBColour.from_rgb(23, 24, 25)) == 17

    # creating the same colour should yield the same curses id
    assert cm.make_colour(RGBColour.from_rgb(12, 13, 14)) == 16

    # once max colours is reached, custom colours should overwrite
    # themselves
    assert cm.make_colour(RGBColour.from_rgb(34, 35, 36)) == 16

    # colour pairs
    assert cm.make_pair(NamedColour("black"), NamedColour("blue")) == 1
    assert cm.make_pair(NamedColour("black"), NamedColour("green")) == 2
    assert cm.make_pair(NamedColour("yellow"), NamedColour("blue")) == 3

    # creating the same pari should yield the same curses id
    assert cm.make_pair(NamedColour("black"), NamedColour("blue")) == 1

    # once max pairs is reached, pairs should overwrite themselves
    assert cm.make_pair(NamedColour("cyan"), NamedColour("white")) == 1
