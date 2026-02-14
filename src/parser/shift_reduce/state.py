from ...grammar import Grammar, Production


class Item:
    """
    Represents a single item in the parsing process.
    Attributes:
        production (Production): The production associated with this item.
        dot (int): The position of the dot in the production's RHS.
        lookahead (frozenset): The lookahead set for LR(1) items. Default is empty for LR(0).
    """

    def __init__(self, production, dot, lookahead=frozenset()):
        self.production = production
        self.dot = dot
        self.lookahead = lookahead

    def __eq__(self, other):
        return (
                self.production == other.production and
                self.dot == other.dot and
                self.lookahead == other.lookahead
        )

    def __hash__(self):
        return hash((self.production, self.dot, tuple(self.lookahead)))

    def __repr__(self):
        return f"Item({self.production}, dot={self.dot}, lookahead={{{', '.join(self.lookahead)}}})"


class State:
    """
    Represents a state in the parsing process.
    Attributes:
        items (set): A set of items in this state.
    """

    def __init__(self, items):
        self.items = frozenset(items)  # Ensure immutability for hashing and comparison

    def __eq__(self, other):
        return self.items == other.items

    def __hash__(self):
        return hash(self.items)

    def __repr__(self):
        return f"State({list(self.items)})"

    def get_kernel(self):
        """Extracts the kernel (core items without lookahead) from the state."""
        return frozenset((item.production, item.dot) for item in self.items)

    def merge(self, other: 'State'):
        """Merges the current state with another state, combining lookaheads."""
        new_lookaheads = {}
        for item in other.items:
            new_lookaheads[item.production, item.dot] = item.lookahead
        for item in self.items:
            new_lookaheads[item.production, item.dot] = item.lookahead.union(
                new_lookaheads[item.production, item.dot]
            )
        return State([
            Item(production, dot, lookahead)
            for (production, dot), lookahead in new_lookaheads.items()
        ])


def lr0_states(grammar: Grammar):
    """
    Constructs LR(0) states for the given grammar.
    Args:
        grammar (Grammar): The grammar for which the LR(0) states are generated.
    Returns:
        Tuple[List[State], dict]: A list of LR(0) states and a dictionary of transitions.
    """
    start_prod = Production("S'", [grammar.start_symbol])
    start_state = State(_lr0_closure(grammar, [Item(start_prod, 0)]))
    states = [start_state]
    state_indices = {start_state: 0}  # Map states to indices
    transitions = {}

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


def lr1_states(grammar: Grammar):
    """
    Constructs LR(1) states for the given grammar.
    Args:
        grammar (Grammar): The grammar for which the LR(1) states are generated.
    Returns:
        Tuple[List[State], dict]: A list of LR(1) states and a dictionary of transitions.
    """
    start_prod = Production("S'", [grammar.start_symbol])
    start_state = State(_lr1_closure(grammar, [Item(start_prod, 0, frozenset({"$"}))]))
    states = [start_state]
    state_indices = {start_state: 0}  # Map states to indices
    transitions = {}

    for i, state in enumerate(states):
        for symbol in grammar.non_terminals.union(grammar.terminals):
            new_state_items = _lr1_successor(grammar, list(state.items), symbol)
            if new_state_items:
                new_state = State(new_state_items)
                if new_state not in state_indices:
                    state_indices[new_state] = len(states)
                    states.append(new_state)
                transitions[(i, symbol)] = state_indices[new_state]


    return states, transitions


def lalr_states(grammar: Grammar):
    """
    Constructs LALR(1) states by merging LR(1) states with the same kernel.
    Args:
        grammar (Grammar): The grammar for which the LALR(1) states are generated.
    Returns:
        Tuple[List[State], dict]: A list of LALR(1) states and a dictionary of transitions.
    """
    start_prod = Production("S'", [grammar.start_symbol])
    start_state = State(_lr1_closure(grammar, [Item(start_prod, 0, frozenset({"$"}))]))

    # Initialize state list and kernel indices
    states = [start_state]
    kernel_indices = {start_state.get_kernel(): 0}  # Map kernels to indices
    transitions = {}
    worklist = [start_state]  # Fixed-point construction using a worklist

    while worklist:
        current_state = worklist.pop()
        current_index = kernel_indices[current_state.get_kernel()]

        for symbol in grammar.non_terminals.union(grammar.terminals):
            new_state_items = _lr1_successor(grammar, list(current_state.items), symbol)
            if new_state_items:
                new_state = State(new_state_items)
                kernel = new_state.get_kernel()

                if kernel not in kernel_indices:
                    kernel_indices[kernel] = len(states)
                    states.append(new_state)
                    worklist.append(new_state)
                else:
                    index = kernel_indices[kernel]
                    old_items = states[index].items
                    states[index] = states[index].merge(new_state)

                    if states[index].items != old_items:
                        worklist.append(states[index])

                transitions[(current_index, symbol)] = kernel_indices[kernel]

    return states, transitions


def merge_lr1_states(states: list[State], transitions: dict):
    """
    Merges LR(1) states with the same kernel into a single state.
    Args:
        states (List[State]): A list of LR(1) states.
        transitions (dict): A dictionary of transitions.
    Returns:
        Tuple[List[State], dict]: A list of merged states and a dictionary of merged transitions.
    """
    kernel_map = {}

    for i, state in enumerate(states):
        kernel = state.get_kernel()
        if kernel not in kernel_map:
            kernel_map[kernel] = []
        kernel_map[kernel].append(i)

    merged_states = []
    state_mapping = {}

    for kernel, state_indices in kernel_map.items():
        merged_state = states[state_indices[0]]
        for index in state_indices[1:]:
            merged_state = merged_state.merge(states[index])
        merged_states.append(merged_state)
        for index in state_indices:
            state_mapping[index] = len(merged_states) - 1

    merged_transitions = {}
    for (state, symbol), target_state in transitions.items():
        merged_source = state_mapping[state]
        merged_target = state_mapping[target_state]
        merged_transitions[(merged_source, symbol)] = merged_target

    return merged_states, merged_transitions

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


def _lr1_closure(grammar: Grammar, items: list[Item]) -> list[Item]:
    closure_set = set(items)
    changed = True

    while changed:
        changed = False
        for item in list(closure_set):
            if item.dot < len(item.production.rhs):
                symbol = item.production.rhs[item.dot]
                if symbol in grammar.non_terminals:
                    remainder = item.production.rhs[item.dot + 1:]
                    first_set = set()
                    for sym in remainder:
                        first_set.update(grammar.first(sym))
                        if '' not in grammar.first(sym):
                            break
                    else:
                        first_set.update(item.lookahead)

                    first_set.discard('')

                    for new_prod in grammar.lookup_productions(symbol):
                        new_item = Item(new_prod, 0, frozenset(first_set))
                        if new_item not in closure_set:
                            closure_set.add(new_item)
                            changed = True

    # Merge lookaheads of like kernels within state
    kernel_dict = {}
    for item in list(closure_set):
        kernel = (item.production, item.dot)
        if kernel not in kernel_dict:
            kernel_dict[kernel] = set(item.lookahead)
        else:
            kernel_dict[kernel].update(item.lookahead)

    return [
        Item(production, dot, frozenset(lookahead))
        for (production, dot), lookahead in kernel_dict.items()
    ]


def _lr1_successor(grammar: Grammar, items: list[Item], symbol: str) -> list[Item]:
    return _lr1_closure(
        grammar,
        [
            Item(item.production, item.dot + 1, item.lookahead)
            for item in items
            if item.dot < len(item.production.rhs) and item.production.rhs[item.dot] == symbol
        ]
    )