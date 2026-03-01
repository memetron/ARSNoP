from __future__ import annotations

from .util import fixed_point
from .closure import augmented_start, lr0_closure, lr1_closure, build_states
from ....grammar.grammar import Grammar
from ..generators.generator import Generator
from ..state import Item, State
from ..types import (
    GotoTable,
    KernelItem,
    LookaheadTable,
    PropagationGraph,
)

class LALR(Generator):
    def _build_states(self, grammar: Grammar):
        states, transitions = build_states(
            grammar,
            [Item(augmented_start(grammar), 0)],
            lr0_closure,
        )
        lookaheads, propagation = _init_lalr_tables(states, grammar)
        _discover_lookaheads(states, transitions, grammar, lookaheads, propagation)
        lookaheads = _propagate_lookaheads(lookaheads, propagation)
        return _build_lalr_states(states, transitions, grammar, lookaheads)

def _init_lalr_tables(
    states: list[State],
    grammar: Grammar,
) -> tuple[LookaheadTable, PropagationGraph]:
    """Initialize lookahead and propagation tables for all kernel items."""
    lookaheads: LookaheadTable = {}
    propagation: PropagationGraph = {}
    for i, state in enumerate(states):
        for kernel in state.get_kernel():
            key: KernelItem = (i, kernel)
            lookaheads[key] = set()
            propagation[key] = set()
    lookaheads[(0, (augmented_start(grammar), 0))].add("$")
    return lookaheads, propagation


_DUMMY = '#'

def _discover_lookaheads(
    states: list[State],
    transitions: GotoTable,
    grammar: Grammar,
    lookaheads: LookaheadTable,
    propagation: PropagationGraph,
) -> None:
    """Compute spontaneous lookaheads and build propagation edges for kernel items.

    Uses a dummy marker to distinguish spontaneous lookaheads (from FIRST of
    following symbols) from propagated ones (dependent on the kernel item's
    own lookahead).  See Dragon Book Algorithm 4.63.
    """
    for i, state in enumerate(states):
        for prod, dot in state.get_kernel():
            kernel_key = (i, (prod, dot))
            initial_items = [Item(prod, dot, frozenset({_DUMMY}))]
            closure = lr1_closure(grammar, initial_items)

            for item in closure:
                if item.is_complete():
                    continue

                symbol = item.production.rhs[item.dot]
                j = transitions.get((i, symbol))
                if j is None:
                    continue

                target: KernelItem = (j, (item.production, item.dot + 1))

                lookaheads[target].update(item.lookahead - {_DUMMY})
                if _DUMMY in item.lookahead:
                    propagation[kernel_key].add(target)


@fixed_point
def _propagate_lookaheads(
    lookaheads: LookaheadTable,
    propagation: PropagationGraph,
) -> LookaheadTable:
    """
    Propagate lookaheads along edges until fixed point.
    """
    new_lookaheads = {k: set(v) for k, v in lookaheads.items()}
    for source, targets in propagation.items():
        for target in targets:
            new_lookaheads[target].update(lookaheads[source])
    return new_lookaheads

def _build_lalr_states(
    states: list[State],
    transitions: GotoTable,
    grammar: Grammar,
    lookaheads: LookaheadTable,
) -> tuple[list[State], GotoTable]:
    """Build final LALR(1) states by applying LR(1) closure with computed lookaheads."""
    lalr: list[State] = []

    for i, state in enumerate(states):
        items: list[Item] = []
        for prod, dot in state.get_kernel():
            la = frozenset(lookaheads[(i, (prod, dot))])
            items.append(Item(prod, dot, la))
        lalr.append(State(lr1_closure(grammar, items)))

    return lalr, transitions