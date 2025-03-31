import abc
import re


class Rule(abc.ABC):
    @abc.abstractmethod
    def matches(self, line: str) -> bool: ...

    @abc.abstractmethod
    def __hash__(self) -> int: ...


class RegexRule(Rule):
    def __init__(self, pattern: str, flags: "re._FlagsType"):
        self.pattern = re.compile(pattern, flags)

    def matches(self, line: str) -> bool:
        return self.pattern.search(line) != None

    def __hash__(self) -> int:
        return hash(self.pattern)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RegexRule):
            return False
        return self.pattern == other.pattern


class LiteralRule(Rule):
    def __init__(self, pattern: str, ignorecase: bool):
        self.ignorecase = ignorecase
        if ignorecase:
            self.pattern = pattern.casefold()
        else:
            self.pattern = pattern

    def matches(self, line: str) -> bool:
        if self.ignorecase:
            line = line.casefold()
        return self.pattern in line

    def __hash__(self) -> int:
        return hash((self.ignorecase, self.pattern))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LiteralRule):
            return False
        return self.pattern == other.pattern and self.ignorecase == other.ignorecase
