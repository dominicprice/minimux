from minimux.utils import strip_ansi


def test_strip_ansi():
    s1 = "\x1b[01;31mGET\x1b[0m"
    assert strip_ansi(s1) == "GET"
