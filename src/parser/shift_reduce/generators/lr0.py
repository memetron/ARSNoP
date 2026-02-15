from __future__ import annotations
from typing import Iterable

from .closure import closure_step

from ....grammar import Grammar, Production
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
    """
    Constructs LR(0) states for the given grammar.
    Args:
        grammar (Grammar): The grammar for which the LR(0) states are generated.
    Returns:
        Tuple[List[State], dict]: A list of LR(0) states and a dictionary of transitions.
    """
    start_prod = Production("S'", [grammar.start_symbol])
    start_state = State(_lr0_closure(grammar, [Item(start_prod, 0)]))
    states: list[State] = [start_state]
    state_indices: dict[State, int] = {start_state: 0}
    transitions: GotoTable = {}

    for i, state in enumerate(states):
        for symbol in grammar.non_terminals.union(grammar.terminals):
            new_state_items = _lr0_successor(grammar, list(state.items), symbol)
            if new_state_items:
                new_state = State(new_state_items)
                if new_state not in state_indices:
                    state_indices[new_state] = len(states)
                    states.append(new_state)
                transitions[(i, symbol)] = state_indices[new_state]
    return states, transitions

def _lr0_closure(grammar: Grammar, items: Iterable[Item]) -> frozenset[Item]:
    return closure_step(frozenset(items), grammar, lambda i, g: frozenset())

def _lr0_successor(grammar: Grammar, items: list[Item], symbol: str) -> frozenset[Item]:
    return _lr0_closure(
        grammar,
        [
            Item(item.production, item.dot + 1)
            for item in items
            if item.dot < len(item.production.rhs) and item.production.rhs[item.dot] == symbol
        ]
    )