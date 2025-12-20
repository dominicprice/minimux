from typing import NamedTuple, Self


class Padding(NamedTuple):
    top: int
    right: int
    bottom: int
    left: int

    @property
    def vertical(self) -> int:
        return self.top + self.bottom

    @property
    def horizontal(self) -> int:
        return self.left + self.right

    @classmethod
    def zero(cls) -> Self:
        return cls(0, 0, 0, 0)

    @classmethod
    def uniform(cls, value: int) -> Self:
        return cls(value, value, value, value)

    @classmethod
    def balanced(cls, top_bottom: int, left_right: int) -> Self:
        return cls(top_bottom, left_right, top_bottom, left_right)

    @classmethod
    def parse(cls, spec: str) -> Self:
        ps = [int(v.strip()) for v in spec.split(",")]
        if len(ps) == 1:
            return cls.uniform(ps[0])
        elif len(ps) == 2:
            return cls.balanced(ps[1], ps[0])
        elif len(ps) == 4:
            return cls(ps[0], ps[1], ps[2], ps[3])
        raise ValueError("expected p or px,py or pt,pr,pb,pl")
