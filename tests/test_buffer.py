from minimux.buffer import Buffer
from minimux.rules import LiteralRule, RegexRule, Rule


def test_buffer():
    rules: dict[Rule, int] = {
        LiteralRule("xyz", False): 1,
        RegexRule("he..o", 0): 2,
    }
    buf = Buffer(20, 5, rules)

    buf.push("line 1")
    buf.push("this line is longer than the twenty character limit")

    assert len(buf.buf) == 4
    assert buf.buf[0] == ("line 1", 0)
    assert buf.buf[1] == ("this line is longer ", 0)
    assert buf.buf[2] == ("than the twenty char", 0)
    assert buf.buf[3] == ("acter limit", 0)

    buf.push("this matches the literal rule xyz")
    assert len(buf.buf) == 5
    assert buf.buf[0] == ("this line is longer ", 0)
    assert buf.buf[1] == ("than the twenty char", 0)
    assert buf.buf[2] == ("acter limit", 0)
    assert buf.buf[3] == ("this matches the lit", 1)
    assert buf.buf[4] == ("eral rule xyz", 1)

    buf.push("regex rule hello")
    assert len(buf.buf) == 5
    assert buf.buf[-1] == ("regex rule hello", 2)
