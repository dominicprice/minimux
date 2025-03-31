import re
from minimux.rules import LiteralRule, RegexRule


def test_regex_rule():
    r = RegexRule("he..o", re.IGNORECASE)
    assert r.matches("a string to say HELLO")
    assert r.matches("is hesdo a word???")
    assert not r.matches("hesssdo")


def test_literal_rule():
    r = LiteralRule("warn", False)
    assert r.matches("i want to warn you")
    assert r.matches("warn")
    assert r.matches("this is a warning")
    assert not r.matches("this is a WARNING")
    assert not r.matches("asdf asdf asdf ")

    r = LiteralRule("info", True)
    assert r.matches("i have some info for you")
    assert r.matches("I hAvE sOmE iNfO fOr YoU")
    assert r.matches("INFO")
    assert not r.matches("iinnnnfooooo!!!")
