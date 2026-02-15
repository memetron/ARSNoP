from __future__ import annotations

from collections.abc import Iterable

from ....grammar import Grammar, Production
from ..automaton import Automaton
from ..generators.generator import Generator
from .lr0 import lr0_states
from .lr1 import _lr1_closure  # pyright: ignore[reportPrivateUsage]
from ..state import Item, State
from ..types import (
    FAKE,
    ActionTable,
    ClosureItem,
    GotoTable,
    KernelItem,
    LookaheadTable,
    PropagationGraph,
)


def lalr_states(grammar: Grammar) -> tuple[list[State], GotoTable]:
    """Construct LALR(1) states using Dragon Book Algorithm 4.63.

    Builds LR(0) states, then determines lookaheads via spontaneous
    generation and propagation, and finally produces full LR(1) states
    with the computed lookaheads.
    """
    states, transitions = lr0_states(grammar)
    lookaheads, propagation = _init_lalr_tables(states, grammar)
    _discover_lookaheads(states, transitions, grammar, lookaheads, propagation)
    _propagate_lookaheads(lookaheads, propagation)
    return _build_lalr_states(states, transitions, grammar, lookaheads)


def _init_lalr_tables(
    states: list[State],
    grammar: Grammar,
) -> tuple[LookaheadTable, PropagationGraph]:
    """Initialize empty lookahead and propagation entries for every kernel item.

    Seeds the start item S' -> . start with the $ lookahead.
    """
    lookaheads: LookaheadTable = {}
    propagation: PropagationGraph = {}

    for i, state in enumerate(states):
        for kernel in state.get_kernel():
            key: KernelItem = (i, kernel)
            lookaheads[key] = set()
            propagation[key] = set()

    start_prod = Production("S'", [grammar.start_symbol])
    lookaheads[(0, (start_prod, 0))].add("$")

    return lookaheads, propagation


def _discover_lookaheads(
    states: list[State],
    transitions: GotoTable,
    grammar: Grammar,
    lookaheads: LookaheadTable,
    propagation: PropagationGraph,
) -> None:
    """For each kernel item, compute closure with the FAKE marker.

    Classifies each resulting lookahead as either spontaneously generated
    (real terminal) or propagated (FAKE marker).
    """
    for i, state in enumerate(states):
        for prod, dot in state.get_kernel():
            closure = _closure_with_fake(
                grammar,
                [(prod, dot, frozenset({FAKE}))]
            )

            for closed_prod, closed_dot, closed_lookahead in closure:
                if closed_dot >= len(closed_prod.rhs):
                    continue

                symbol: str = closed_prod.rhs[closed_dot]
                j = transitions.get((i, symbol))
                if j is None:
                    continue

                target: KernelItem = (j, (closed_prod, closed_dot + 1))
                source: KernelItem = (i, (prod, dot))

                for terminal in closed_lookahead:
                    if terminal == FAKE:
                        propagation[source].add(target)
                    else:
                        lookaheads[target].add(terminal)


def _propagate_lookaheads(
    lookaheads: LookaheadTable,
    propagation: PropagationGraph,
) -> None:
    """Fixed-point loop: copy lookaheads along propagation edges until stable."""
    changed = True
    while changed:
        changed = False
        for source, targets in propagation.items():
            for target in targets:
                before = len(lookaheads[target])
                lookaheads[target].update(lookaheads[source])
                if len(lookaheads[target]) != before:
                    changed = True


def _build_lalr_states(
    states: list[State],
    transitions: GotoTable,
    grammar: Grammar,
    lookaheads: LookaheadTable,
) -> tuple[list[State], GotoTable]:
    """Attach computed lookaheads to LR(0) kernels and compute LR(1) closure."""
    lalr: list[State] = []

    for i, state in enumerate(states):
        items: list[Item] = []
        for prod, dot in state.get_kernel():
            la = frozenset(lookaheads[(i, (prod, dot))])
            items.append(Item(prod, dot, la))
        lalr.append(State(_lr1_closure(grammar, items)))

    return lalr, transitions


def _closure_with_fake(
    grammar: Grammar,
    items: Iterable[ClosureItem],
) -> set[ClosureItem]:
    """Compute LR(1) closure using the FAKE sentinel as a placeholder lookahead.

    The FAKE marker (``#``) stands in for unknown lookaheads during the
    discovery phase of Algorithm 4.63.  When a FAKE marker survives into the
    closure result, it indicates that the lookahead propagates from the
    source kernel item rather than being generated spontaneously.
    """
    closure: set[ClosureItem] = set(items)

    changed = True
    while changed:
        changed = False

        for prod, dot, lookahead in list(closure):
            if dot >= len(prod.rhs):
                continue

            nonterminal: str = prod.rhs[dot]
            if nonterminal not in grammar.non_terminals:
                continue

            beta: list[str] = prod.rhs[dot + 1:]

            first: set[str] = set()
            nullable = True

            for sym in beta:
                sym_first: set[str] = grammar.first(sym)
                first.update(sym_first - {''})
                if '' not in sym_first:
                    nullable = False
                    break

            if nullable:
                first.update(lookahead)

            first.discard('')

            for new_prod in grammar.lookup_productions(nonterminal):
                new_item: ClosureItem = (new_prod, 0, frozenset(first))
                if new_item not in closure:
                    closure.add(new_item)
                    changed = True

    return closure


class LALR(Generator):
    """
    Class for generating LALR(1) parsing tables.
    Creates the tables by merging LR(1) states as they are generated
    Methods:
        generate(grammar: Grammar): Generates LALR(1) automaton.
    """
    def generate(self, grammar: Grammar) -> Automaton:
        goto: GotoTable = {}
        action: ActionTable = {}
        states, transitions = lalr_states(grammar)

        for i, state in enumerate(states):
            for item in state.items:
                if item.dot == len(item.production.rhs):  # Reduce or Accept state
                    if item.production.lhs == "S'":
                        action[(i, '$')] = ("accept",)
                    else:
                        for terminal in item.lookahead:
                            action[(i, terminal)] = ("reduce", item.production)
                elif item.dot < len(item.production.rhs):  # Shift state
                    symbol = item.production.rhs[item.dot]
                    if symbol in grammar.terminals:
                        next_state = transitions.get((i, symbol))
                        if next_state is not None:
                            action[(i, symbol)] = ("shift", next_state)

            for non_terminal in grammar.non_terminals:
                next_state = transitions.get((i, non_terminal))
                if next_state is not None:
                    goto[(i, non_terminal)] = next_state

        return Automaton(goto, action)
