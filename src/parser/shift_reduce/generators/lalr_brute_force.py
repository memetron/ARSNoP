from __future__ import annotations

from ....grammar.production import Production
from ....grammar import Grammar
from ..automaton import Automaton
from ..generators.generator import Generator
from .lr1 import _lr1_closure, lr1_states # type: ignore
from ..state import Item, State
from ..types import GotoTable, ActionTable, Kernel

def _merge_state(state: State, other: State, grammar: Grammar) -> State:
        """Merges two states by unioning lookaheads for identical kernel items and recomputing closure."""
        merged_items_dict: dict[tuple[Production, int], frozenset[str]] = {}
        for item in state.items.union(other.items):
            key = (item.production, item.dot)
            if key in merged_items_dict:
                merged_items_dict[key] = merged_items_dict[key].union(item.lookahead)
            else:
                merged_items_dict[key] = item.lookahead
        merged_items = [Item(prod, dot, la) for (prod, dot), la in merged_items_dict.items()]
        return State(_lr1_closure(grammar, merged_items))

def _merge_lr1_states(states: list[State], transitions: GotoTable, grammar: Grammar) -> tuple[list[State], GotoTable]:
    """
    Merge LR(1) states with the same kernel into a single state, unioning lookaheads.
    Args:
        states: List of LR(1) states.
        transitions: Original LR(1) GotoTable.
    Returns:
        merged_states, merged_transitions
    """
    # Step 1: Group states by kernel
    kernel_map: dict[Kernel, list[int]] = {}
    for idx, state in enumerate(states):
        kernel = state.get_kernel()
        kernel_map.setdefault(kernel, []).append(idx)

    # Step 2: Merge states per kernel
    merged_states: list[State] = []
    old_to_merged: dict[int, int] = {}
    for kernel_indices in kernel_map.values():
        # Start with the first state
        merged_state = states[kernel_indices[0]]
        for idx in kernel_indices[1:]:
            merged_state = _merge_state(merged_state, states[idx], grammar)
        merged_states.append(merged_state)
        merged_idx = len(merged_states) - 1
        for old_idx in kernel_indices:
            old_to_merged[old_idx] = merged_idx

    # Step 3: Remap transitions to merged state indices
    merged_transitions: GotoTable = {}
    for (src, symbol), tgt in transitions.items():
        merged_src = old_to_merged[src]
        merged_tgt = old_to_merged[tgt]
        merged_transitions[(merged_src, symbol)] = merged_tgt

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
        states, transitions = _merge_lr1_states(*lr1_states(grammar), grammar)
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
