from __future__ import annotations

from ...grammar import Grammar, Production
from .automaton import Automaton
from .generators import Generator
from .state import Item, State
from .types import GotoTable, ActionTable


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


def _lr0_closure(grammar: Grammar, items: list[Item]) -> list[Item]:
    closure_set = set(items)
    changed = True
    while changed:
        changed = False
        for item in list(closure_set):
            if item.dot < len(item.production.rhs):
                symbol = item.production.rhs[item.dot]
                if symbol in grammar.non_terminals:
                    for new_prod in grammar.lookup_productions(symbol):
                        new_item = Item(new_prod, 0)
                        if new_item not in closure_set:
                            closure_set.add(new_item)
                            changed = True
    return list(closure_set)


def _lr0_successor(grammar: Grammar, items: list[Item], symbol: str) -> list[Item]:
    return _lr0_closure(
        grammar,
        [
            Item(item.production, item.dot + 1)
            for item in items
            if item.dot < len(item.production.rhs) and item.production.rhs[item.dot] == symbol
        ]
    )


class LR0(Generator):
    """
    Class for generating LR(0) parsing tables.
    Methods:
        generate(grammar: Grammar): Generates LR(0) automaton
    """
    def generate(self, grammar: Grammar) -> Automaton:
        goto: GotoTable = {}
        action: ActionTable = {}
        states, transitions = lr0_states(grammar)

        for i, state in enumerate(states):
            for item in state.items:
                if item.dot == len(item.production.rhs):  # Reduce or Accept state
                    if item.production.lhs == "S'":
                        action[(i, '$')] = ("accept",)
                    else:
                        for terminal in grammar.terminals | {'$'}:
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


class SLR(Generator):
    """
    Class for generating SLR(1) parsing tables.
    Methods:
        generate(grammar: Grammar): Generates SLR(1) automaton.
    """
    def generate(self, grammar: Grammar) -> Automaton:
        goto: GotoTable = {}
        action: ActionTable = {}
        states, transitions = lr0_states(grammar)

        for i, state in enumerate(states):
            for item in state.items:
                if item.dot == len(item.production.rhs):  # Reduce or Accept state
                    if item.production.lhs == "S'":
                        action[(i, '$')] = ("accept",)
                    else:
                        for terminal in grammar.follow(item.production.lhs):
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
