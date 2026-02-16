from dataclasses import dataclass


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

    def __str__(self) -> str:
        return f"{self.lhs} ::= {' '.join(self.rhs)}"
