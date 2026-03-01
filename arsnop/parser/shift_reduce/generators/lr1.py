from __future__ import annotations

from .closure import augmented_start, build_states, lr1_closure
from ....grammar.grammar import Grammar
from ..generators.generator import Generator
from ..state import Item, State
from ..types import GotoTable


class LR1(Generator):
    def _build_states(self, grammar: Grammar):
        return lr1_states(grammar)

def lr1_states(grammar: Grammar) -> tuple[list[State], GotoTable]:
    """Constructs LR(1) states for the given grammar."""
    start_items = [Item(augmented_start(grammar), 0, frozenset({"$"}))]
    return build_states(grammar, start_items, lr1_closure)
