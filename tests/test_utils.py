from minimux.utils import Counter, UniqueDict


def test_counter():
    c = Counter(1, 5)
    assert c() == 1
    assert c() == 2
    assert c() == 3
    assert c() == 4
    assert c() == 5
    assert c() == 1


def test_inverse_dict():
    d: UniqueDict[str, int] = UniqueDict()

    d["hello"] = 1
    d["bye"] = 2
    assert d["hello"] == 1
    assert d["bye"] == 2

    d["mate"] = 1
    assert "hello" not in d
    assert d["bye"] == 2
    assert d["mate"] == 1
