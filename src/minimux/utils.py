from typing import TypeVar

T = TypeVar("T")


def combine(t1: T, t2: T) -> T:
    if t2 is None:
        return t1
    return t2
