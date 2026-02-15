from __future__ import annotations

from ....grammar.production import Production
from ....grammar import Grammar
from ..generators.generator import Generator
from .lr1 import _lr1_closure, lr1_states # type: ignore
from ..state import Item, State
from ..types import GotoTable, Kernel

class LALR_Brute_Force(Generator):
    def _build_states(self, grammar: Grammar):
        states, transitions = lr1_states(grammar)
        kernel_map: dict[Kernel, list[int]] = {}
        for idx, state in enumerate(states):
            kernel = state.get_kernel()
            kernel_map.setdefault(kernel, []).append(idx)

        merged_states: list[State] = []
        old_to_merged: dict[int, int] = {}
        for kernel_indices in kernel_map.values():
            merged_state = states[kernel_indices[0]]
            for idx in kernel_indices[1:]:
                merged_state = _merge_state(merged_state, states[idx], grammar)
            merged_states.append(merged_state)
            merged_idx = len(merged_states) - 1
            for old_idx in kernel_indices:
                old_to_merged[old_idx] = merged_idx

        merged_transitions: GotoTable = {}
        for (src, symbol), tgt in transitions.items():
            merged_src = old_to_merged[src]
            merged_tgt = old_to_merged[tgt]
            merged_transitions[(merged_src, symbol)] = merged_tgt

        return merged_states, merged_transitions

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