from __future__ import annotations

from typing import Any, cast
from .parser.shift_reduce.state import State


def flatten(arr: Any) -> list[Any]:
    if isinstance(arr, list):
        result: list[Any] = []
        for sublist in cast(list[Any], arr):
            result.extend(flatten(sublist))
        return result
    return [arr]


def print_states(states: list[State]) -> None:
    for index, state in enumerate(states):
        print(f"STATE_{index}:")
        for item in state.items:
            production = f"{item.production.lhs} ::= {' '.join(item.production.rhs[:item.dot] + ['.'] + item.production.rhs[item.dot:])} ({str(list(item.lookahead))})"
            print(f"\t{production}")
