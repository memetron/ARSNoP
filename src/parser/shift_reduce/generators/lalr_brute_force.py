from __future__ import annotations

from .closure import augmented_start, build_states, lr1_closure
from ....grammar.production import Production
from ....grammar import Grammar
from ..generators.generator import Generator
from ..state import Item, State
from ..types import GotoTable, Kernel

class LALR_Brute_Force(Generator):
    def _build_states(self, grammar: Grammar):
        states, transitions = build_states(
            grammar,
            [Item(augmented_start(grammar), 0, frozenset({"$"}))],
            lr1_closure,
        )
        kernel_map = _group_by_kernel(states)
        merged_states, old_to_merged = _merge_states(states, kernel_map, grammar)
        merged_transitions = _remap_transitions(transitions, old_to_merged)
        return merged_states, merged_transitions


def _group_by_kernel(states: list[State]) -> dict[Kernel, list[int]]:
    """Group state indices by their LR(0) kernel."""
    kernel_map: dict[Kernel, list[int]] = {}
    for idx, state in enumerate(states):
        kernel_map.setdefault(state.get_kernel(), []).append(idx)
    return kernel_map


def _merge_states(
    states: list[State],
    kernel_map: dict[Kernel, list[int]],
    grammar: Grammar,
) -> tuple[list[State], dict[int, int]]:
    """Merge states that share a kernel by unioning their lookaheads."""
    merged_states: list[State] = []
    old_to_merged: dict[int, int] = {}
    for kernel_indices in kernel_map.values():
        merged_state = states[kernel_indices[0]]
        for idx in kernel_indices[1:]:
            merged_state = _merge_two(merged_state, states[idx], grammar)
        merged_idx = len(merged_states)
        merged_states.append(merged_state)
        for old_idx in kernel_indices:
            old_to_merged[old_idx] = merged_idx
    return merged_states, old_to_merged


def _merge_two(state: State, other: State, grammar: Grammar) -> State:
    """Merge two states by unioning lookaheads for identical kernel items and recomputing closure."""
    merged_items_dict: dict[tuple[Production, int], frozenset[str]] = {}
    for item in state.items.union(other.items):
        key = (item.production, item.dot)
        if key in merged_items_dict:
            merged_items_dict[key] = merged_items_dict[key].union(item.lookahead)
        else:
            merged_items_dict[key] = item.lookahead
    merged_items = [Item(prod, dot, la) for (prod, dot), la in merged_items_dict.items()]
    return State(lr1_closure(grammar, merged_items))


def _remap_transitions(
    transitions: GotoTable,
    old_to_merged: dict[int, int],
) -> GotoTable:
    """Remap transition indices from the original states to the merged states."""
    return {
        (old_to_merged[src], symbol): old_to_merged[tgt]
        for (src, symbol), tgt in transitions.items()
    }
