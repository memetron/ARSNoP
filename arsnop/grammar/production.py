from dataclasses import dataclass
from enum import StrEnum


class Modifier(StrEnum):
    """EBNF modifiers for rule alternatives."""

    OPT = "opt"
    STAR = "star"
    PLUS = "plus"

@dataclass(frozen=True)
class Production:
    """
    A production rule in a context-free grammar.
    Attributes:
        lhs: The left-hand side non-terminal.
        rhs: The right-hand side symbols (terminals or non-terminals).
    """

    lhs: str
    rhs: tuple[str, ...]
    modifier: Modifier | None = None

    def __str__(self) -> str:
        return f"{self.lhs} ::= {' '.join(self.rhs)}"
