from __future__ import annotations

from ....grammar import Grammar, Production
from ..automaton import Automaton
from ..generators.generator import Generator
from .lr1 import lr1_states
from ..state import State
from ..types import GotoTable, ActionTable


def merge_lr1_states(states: list[State], transitions: GotoTable) -> tuple[list[State], GotoTable]:
    """
    Merges LR(1) states with the same kernel into a single state.
    Args:
        states (List[State]): A list of LR(1) states.
        transitions (dict): A dictionary of transitions.
    Returns:
        Tuple[List[State], dict]: A list of merged states and a dictionary of merged transitions.
    """
    kernel_map: dict[frozenset[tuple[Production, int]], list[int]] = {}

    for i, state in enumerate(states):
        kernel = state.get_kernel()
        if kernel not in kernel_map:
            kernel_map[kernel] = []
        kernel_map[kernel].append(i)

    merged_states: list[State] = []
    state_mapping: dict[int, int] = {}

    for kernel, state_indices_list in kernel_map.items():
        merged_state = states[state_indices_list[0]]
        for index in state_indices_list[1:]:
            merged_state = merged_state.merge(states[index])
        merged_states.append(merged_state)
        for index in state_indices_list:
            state_mapping[index] = len(merged_states) - 1

    merged_transitions: GotoTable = {}
    for (state_idx, symbol), target_state in transitions.items():
        merged_source = state_mapping[state_idx]
        merged_target = state_mapping[target_state]
        merged_transitions[(merged_source, symbol)] = merged_target

    return merged_states, merged_transitions


class LALR_Brute_Force(Generator):
    """
    Class for generating LALR(1) parsing tables.
    Creates the tables via brute force merging LR(1) states
    Methods:
        generate(grammar: Grammar): Generates LALR(1) automaton.
    """
    def generate(self, grammar: Grammar) -> Automaton:
        goto: GotoTable = {}
        action: ActionTable = {}
        states, transitions = merge_lr1_states(*lr1_states(grammar))
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
