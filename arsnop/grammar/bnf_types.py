"""Result types produced by the BNF parser."""
from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class Rhs:
    """One alternative in a rule (empty symbols tuple → nullable production)."""

    symbols: tuple[str, ...]


@dataclass(frozen=True)
class RuleSpec:
    """A single grammar rule: lhs ::= alt1 | alt2 | ..."""

    lhs: str
    alternatives: tuple[Rhs, ...]
    inline: bool = False


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