import curses
from typing import Generic, TypeVar

T = TypeVar("T")


def combine(t1: T, t2: T | None) -> T:
    "return t1 if t2 is None, else t2"
    if t2 is None:
        return t1
    return t2


def char_eq(a: int, b: int) -> bool:
    "returns True if a and b are equal characters, ignoring attributes"
    return (a & curses.A_CHARTEXT) == (b & curses.A_CHARTEXT)


def split_list(v: str) -> list[str]:
    "converts a comma separated string into a list, omitting empty elements"
    res: list[str] = []
    for elem in v.split(","):
        e = elem.strip()
        if e:
            res.append(e)
    return res


class Counter:
    def __init__(self, min_value: int, max_value: int):
        self.value = min_value
        self.min_value = min_value
        self.max_value = max_value

    def __call__(self) -> int:
        res = self.value
        self.value += 1
        if self.value > self.max_value:
            self.value = self.min_value
        return res

    def clamp(self):
        self.min_value = self.value


K = TypeVar("K")
V = TypeVar("V")


class UniqueDict(Generic[K, V]):
    """
    UniqueDict ensures that each value is unique, removing old keys
    if a new key with the same value is added
    """

    def __init__(self):
        self.forward: dict[K, V] = {}
        self.backward: dict[V, K] = {}

    def __setitem__(self, key: K, value: V):
        if key in self.forward:
            del self.backward[self.forward[key]]
        self.forward[key] = value
        if value in self.backward:
            del self.forward[self.backward[value]]
        self.backward[value] = key

    def __getitem__(self, key: K) -> V:
        return self.forward[key]

    def __contains__(self, key: K) -> bool:
        return key in self.forward

    def __len__(self) -> int:
        return len(self.forward)
