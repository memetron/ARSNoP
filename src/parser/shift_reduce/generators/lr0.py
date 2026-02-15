from __future__ import annotations
from typing import Iterable

from .closure import augmented_start, build_states, lr0_closure

from ....grammar import Grammar
from ..generators.generator import Generator
from ..state import Item, State
from ..types import GotoTable

class LR0(Generator):
    def _build_states(self, grammar: Grammar):
        return lr0_states(grammar)

    def _reduce_lookaheads(self, grammar: Grammar, item: Item) -> Iterable[str]:
        return grammar.terminals.union({'$'})

class SLR(Generator):
    def _build_states(self, grammar: Grammar):
        return lr0_states(grammar)

    def _reduce_lookaheads(self, grammar: Grammar, item: Item) -> Iterable[str]:
        if item.production.lhs == "S'":
            return {'$'}
        return grammar.follow(item.production.lhs)

def lr0_states(grammar: Grammar) -> tuple[list[State], GotoTable]:
    """Constructs LR(0) states for the given grammar."""
    start_items = [Item(augmented_start(grammar), 0)]
    return build_states(grammar, start_items, lr0_closure)
