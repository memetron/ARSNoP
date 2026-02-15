from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Callable

from ....grammar import Grammar
from ..automaton import Automaton
from ..types import Action, ActionEntry, ActionTable, GotoTable
from ..state import Item, State

class Generator(ABC):
    """
    Base class for LR-family parsing table generators.

    Subclasses must define:
        _build_states(grammar)
        _reduce_lookaheads(grammar, item)
    """

    def generate(self, grammar: Grammar) -> Automaton:
        states, transitions = self._build_states(grammar)
        action = _build_action_table(
            grammar,
            states,
            transitions,
            self._reduce_lookaheads,
        )
        goto = _build_goto_table(grammar, transitions)
        return Automaton(goto, action)

    # --- Required overrides ---

    @abstractmethod
    def _build_states(
        self,
        grammar: Grammar,
    ) -> tuple[list[State], GotoTable]:
        ...

    def _reduce_lookaheads(
        self,
        grammar: Grammar,
        item: Item,
    ) -> Iterable[str]:
        return item.lookahead


def _build_action_table(
    grammar: Grammar,
    states: list[State],
    transitions: GotoTable,
    lookahead_fn: Callable[[Grammar, Item], Iterable[str]],
) -> ActionTable:
    entries: dict[tuple[int, str], Action] = {}

    for i, state in enumerate(states):
        for item in state.items:
            if item.is_complete():
                for entry in _reduce_or_accept_actions(
                    i, item, lookahead_fn(grammar, item),
                ):
                    entries[entry[0]] = entry[1]
            else:
                for entry in _shift_actions(grammar, transitions, i, item):
                    entries[entry[0]] = entry[1]

    return entries


def _build_goto_table(
    grammar: Grammar,
    transitions: GotoTable,
) -> GotoTable:
    return {
        (state, symbol): next_state
        for (state, symbol), next_state in transitions.items()
        if symbol in grammar.non_terminals
    }


def _shift_actions(
    grammar: Grammar,
    transitions: GotoTable,
    state_index: int,
    item: Item,
) -> Iterable[ActionEntry]:
    symbol = item.production.rhs[item.dot]
    if symbol not in grammar.terminals:
        return
    next_state = transitions.get((state_index, symbol))
    if next_state is not None:
        yield ((state_index, symbol), ("shift", next_state))


def _reduce_or_accept_actions(
    state_index: int,
    item: Item,
    lookaheads: Iterable[str],
) -> Iterable[ActionEntry]:
    if item.production.lhs == "S'":
        yield ((state_index, '$'), ("accept",))
        return
    for terminal in lookaheads:
        yield ((state_index, terminal), ("reduce", item.production))
