from __future__ import annotations

from collections.abc import Iterable
from typing import Callable

from ..state import Item, State
from .util import fixed_point
from ....grammar.grammar import Grammar
from ....grammar.production import Production
from ..types import GotoTable


type LookaheadFn = Callable[[Item, Grammar], frozenset[str]]
type ClosureFn = Callable[[Grammar, Iterable[Item]], frozenset[Item]]

@fixed_point
def closure_step(
    closure: frozenset[Item],
    grammar: Grammar,
    lookaheadFn: LookaheadFn
) -> frozenset[Item]:
    """Expand closure by one step, merging lookaheads for identical (production, dot) cores."""
    lookaheads_dict: dict[Item, set[str]] = {}

    for item in closure:
        lookaheads_dict.setdefault(item.without_lookahead(), set()).update(item.lookahead)

    for item in closure:
        if item.is_complete():
            continue
        symbol = item.production.rhs[item.dot]
        if symbol in grammar.non_terminals:
            for new_prod in grammar.lookup_productions(symbol):
                la = lookaheadFn(item, grammar)
                new_item: Item = Item(new_prod, 0)
                lookaheads_dict.setdefault(new_item, set()).update(la)

    return frozenset(
        item.with_lookahead(frozenset(la))
        for item, la in lookaheads_dict.items()
    )


def augmented_start(grammar: Grammar) -> Production:
    """Return the augmented start production S' -> start_symbol."""
    return Production("S'", (grammar.start_symbol,))


def lr1_lookahead(item: Item, grammar: Grammar) -> frozenset[str]:
    """Compute FIRST of the remaining RHS symbols plus item's lookahead."""
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


def lr0_closure(grammar: Grammar, items: Iterable[Item]) -> frozenset[Item]:
    """Compute LR(0) closure (no lookahead propagation)."""
    return closure_step(frozenset(items), grammar, lambda _i, _g: frozenset())


def lr1_closure(grammar: Grammar, items: Iterable[Item]) -> frozenset[Item]:
    """Compute LR(1) closure with lookahead propagation."""
    return closure_step(frozenset(items), grammar, lr1_lookahead)


def successor(
    grammar: Grammar,
    items: Iterable[Item],
    symbol: str,
    closure_fn: ClosureFn,
) -> frozenset[Item]:
    """Advance the dot past *symbol* in matching items, then close."""
    advanced = [
        Item(item.production, item.dot + 1, item.lookahead)
        for item in items
        if item.dot < len(item.production.rhs)
        and item.production.rhs[item.dot] == symbol
    ]
    return closure_fn(grammar, advanced)


def build_states(
    grammar: Grammar,
    start_items: Iterable[Item],
    closure_fn: ClosureFn,
) -> tuple[list[State], GotoTable]:
    """BFS loop that builds all states and transitions for a given closure function."""
    start_state = State(closure_fn(grammar, start_items))
    states: list[State] = [start_state]
    state_indices: dict[State, int] = {start_state: 0}
    transitions: GotoTable = {}

    for i, state in enumerate(states):
        for symbol in grammar.non_terminals.union(grammar.terminals):
            new_state_items = successor(grammar, state.items, symbol, closure_fn)
            if new_state_items:
                new_state = State(new_state_items)
                if new_state not in state_indices:
                    state_indices[new_state] = len(states)
                    states.append(new_state)
                transitions[(i, symbol)] = state_indices[new_state]

    return states, transitions
