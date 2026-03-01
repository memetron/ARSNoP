"""Result types produced by the BNF parser."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

class InlineType(Enum):
    NONE = 0
    INLINE = 1
    CONDITIONAL_INLINE = 2
    
@dataclass(frozen=True)
class Rhs:
    """One alternative in a rule (empty symbols tuple → nullable production)."""

    symbols: tuple[str, ...]
    label: str | None = None
    
    def with_label(self, label: str) -> Rhs:
        return Rhs(symbols=self.symbols, label=label)

@dataclass(frozen=True)
class RuleSpec:
    """A single grammar rule: lhs ::= alt1 | alt2 | ..."""

    lhs: str
    alternatives: tuple[Rhs, ...]
    inline: InlineType = InlineType.NONE


@dataclass(frozen=True)
class BnfSpec:
    """The complete parsed BNF file."""

    rules: tuple[RuleSpec, ...]
    terminals: tuple[TerminalSpec, ...]
    ignored: tuple[str, ...]

@dataclass(frozen=True)
class TerminalSpec:
    """A single terminal definition: name pattern."""

    name: str
    pattern: str
    inline: bool = False