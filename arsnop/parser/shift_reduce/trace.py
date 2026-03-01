"""Trace types for shift-reduce parsing."""

from __future__ import annotations

from dataclasses import dataclass

from ...grammar.production import Production
from ...lexer import Token
from ...ast import AST


@dataclass(frozen=True)
class TraceAction:
    """A single action taken during shift-reduce parsing."""

    type: str
    state: int | None = None
    production: Production | None = None


@dataclass(frozen=True)
class TraceStep:
    """A snapshot of one step during shift-reduce parsing."""

    step: int
    stack: tuple[int, ...]
    input_buffer: tuple[Token, ...]
    action: TraceAction


@dataclass(frozen=True)
class ShiftReduceTrace:
    """The full result of a traced shift-reduce parse."""

    tokens: tuple[Token, ...]
    steps: tuple[TraceStep, ...]
    ast: AST | None
    error: str | None = None
