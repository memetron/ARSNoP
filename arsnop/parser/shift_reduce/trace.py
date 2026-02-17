"""Trace types for shift-reduce parsing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ...grammar import Production
from ...lexer import Token
from ..ast import AST
from .types import Action


@dataclass(frozen=True)
class TraceAction:
    """A single action taken during shift-reduce parsing."""

    type: Literal["shift", "reduce", "accept"]
    state: int | None = None
    production: Production | None = None

    @classmethod
    def from_action(cls, action: Action) -> TraceAction:
        """Convert an Action tuple to a TraceAction dataclass."""
        if action[0] == "shift":
            return cls(type="shift", state=action[1])
        elif action[0] == "reduce":
            return cls(type="reduce", production=action[1])
        else:
            return cls(type="accept")


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
