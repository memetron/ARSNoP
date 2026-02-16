"""Trace types for Earley parsing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ...grammar import Production
from ...lexer import Token
from ..ast import AST


@dataclass(frozen=True)
class TracedEarleyItem:
    """An Earley item annotated with the operation that created it."""

    production: Production
    dot: int
    origin: int
    operation: Literal["init", "predict", "scan", "complete"]


@dataclass(frozen=True)
class EarleyColumn:
    """One column in the Earley chart."""

    index: int
    token: Token | None
    items: tuple[TracedEarleyItem, ...]


@dataclass(frozen=True)
class EarleyTrace:
    """The full result of a traced Earley parse."""

    tokens: tuple[Token, ...]
    chart: tuple[EarleyColumn, ...]
    ast: AST | None
    error: str | None = None
