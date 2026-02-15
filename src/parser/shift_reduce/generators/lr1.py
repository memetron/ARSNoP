from __future__ import annotations
from typing import Iterable

from .closure import closure_step
from ....grammar import Grammar, Production
from ..generators.generator import Generator
from ..state import Item, State
from ..types import GotoTable


class LR1(Generator):
    def _build_states(self, grammar: Grammar):
        return lr1_states(grammar)

def lr1_states(grammar: Grammar) -> tuple[list[State], GotoTable]:
    """
    Constructs LR(1) states for the given grammar.
    Args:
        grammar (Grammar): The grammar for which the LR(1) states are generated.
    Returns:
        Tuple[List[State], dict]: A list of LR(1) states and a dictionary of transitions.
    """
    start_prod = Production("S'", [grammar.start_symbol])
    start_state = State(_lr1_closure(grammar, [Item(start_prod, 0, frozenset({"$"}))]))
    states: list[State] = [start_state]
    state_indices: dict[State, int] = {start_state: 0}
    transitions: GotoTable = {}

    for i, state in enumerate(states):
        for symbol in grammar.non_terminals.union(grammar.terminals):
            new_state_items = _lr1_successor(grammar, list(state.items), symbol)
            if new_state_items:
                new_state = State(new_state_items)
                if new_state not in state_indices:
                    state_indices[new_state] = len(states)
                    states.append(new_state)
                transitions[(i, symbol)] = state_indices[new_state]

    return states, transitions


def _lr1_lookahead(item: Item, grammar: Grammar) -> frozenset[str]:
    remainder = item.production.rhs[item.dot + 1:]
    first: set[str] = set()

    for sym in remainder:
        sym_first = grammar.first(sym)
        first.update(sym_first - {''})
        if '' not in sym_first:
            break
    else:
        first.update(item.lookahead)

    first.discard('')
    return frozenset(first)

def _lr1_closure(grammar: Grammar, items: Iterable[Item]) -> frozenset[Item]:
    return closure_step(frozenset(items), grammar, _lr1_lookahead)

def _lr1_successor(grammar: Grammar, items: list[Item], symbol: str) -> frozenset[Item]:
    return _lr1_closure(
        grammar,
        [
            Item(item.production, item.dot + 1, item.lookahead)
            for item in items
            if item.dot < len(item.production.rhs) and item.production.rhs[item.dot] == symbol
        ]
    )