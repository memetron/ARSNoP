from __future__ import annotations

from typing import Callable, TypeVar

from ..state import Item
from .util import fixed_point
from ....grammar.grammar import Grammar

ItemT = TypeVar("ItemT")

type LookaheadFn = Callable[[Item, Grammar], frozenset[str]]

@fixed_point
def closure_step(
    closure: frozenset[Item],
    grammar: Grammar,
    compute_lookahead: LookaheadFn
) -> frozenset[Item]:
    new_items = set(closure)
    for item in closure:
        if item.dot >= len(item.production.rhs):
            continue
        symbol = item.production.rhs[item.dot]
        if symbol in grammar.non_terminals:
            for new_prod in grammar.lookup_productions(symbol):
                new_items.add(Item(new_prod, 0, compute_lookahead(item, grammar)))
    return frozenset(new_items)