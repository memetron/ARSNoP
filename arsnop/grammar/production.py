from dataclasses import dataclass

from arsnop.grammar.bnf_types import InlineType


@dataclass(frozen=True)
class Production:
    """
    A production rule in a context-free grammar.
    Attributes:
        lhs: The left-hand side non-terminal.
        rhs: The right-hand side symbols (terminals or non-terminals).
        inline: True for EBNF-generated auxiliary rules whose children are
            spliced into the parent node rather than wrapped in their own AST node.
    """

    lhs: str
    rhs: tuple[str, ...]
    inline: InlineType = InlineType.NONE
    label: str | None = None

    def __str__(self) -> str:
        return f"{self.lhs} ::= {' '.join(self.rhs)}"
