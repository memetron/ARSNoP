from __future__ import annotations

from ...grammar.grammar import Grammar
from ...grammar.production import Production
from ...lexer import Token


class State:
    """
    Represents a state in the Earley parser for a specific input symbol.
    Attributes:
        items (set[Item]): The set of items within the state.
        index (int): The index of the input associated with this state.
    """

    def __init__(self, grammar: Grammar, items: set['Item'], index: int):
        """
        Initializes a State instance.
        Args:
            grammar (Grammar): The grammar to act upon.
            items (set[Item]): The initial set of items in the state.
            index (int): The index of the input this state corresponds to.
        """
        self.index = index
        self.items = _closure(grammar, items, index)

    def successor(self, symbol: str, matched_by: Token | None = None) -> set[Item]:
        """
        Generates a new set of items after transitioning on a given symbol.
        Args:
            symbol (str): The symbol to transition on.
            matched_by (Token): The token that matches this symbol.
        Returns:
            set[Item]: A set of items waiting on the given symbol.
        """
        new_items: set[Item] = set()
        for item in self.items:
            if not item.is_completed() and item.get_next_symbol() == symbol:
                new_item = Item(item.production, item.dot + 1, item.input_position)
                new_item.prev_step = item
                new_item.matched_token = matched_by
                new_items.add(new_item)
        return new_items

    def __str__(self) -> str:
        return "\n".join(map(str, self.items))


class Item:
    """
    Represents a single parsing rule in a specific state.
    Attributes:
        production (Production): The production rule for this item.
        dot (int): Position within the production rule that has been matched.
        input_position (int): Index in the input where the rule starts matching.
        prev_step (Item): The previous item that transitioned to this one.
        matched_token (Token | None): The terminal token that was scanned at this step.
        completed_by (Item | None): The completed item that proved a non-terminal at this step.
    """

    def __init__(self, production: Production, dot: int, input_position: int):
        """
        Initializes an Item instance.
        Args:
            production (Production): The production rule associated with the item.
            dot (int): Position of the dot in the production rule.
            input_position (int): Input index where the rule starts matching.
        """
        self.production = production
        self.dot = dot
        self.input_position = input_position
        self.prev_step: Item | None = None
        self.matched_token: Token | None = None
        self.completed_by: Item | None = None

    def is_completed(self) -> bool:
        """Checks if the production rule has been fully matched."""
        return self.dot == len(self.production.rhs)

    def get_next_symbol(self) -> str:
        """Gets the symbol immediately following the dot in the production rule."""
        return self.production.rhs[self.dot]

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Item) and
            self.production == other.production and
            self.dot == other.dot and
            self.input_position == other.input_position
        )

    def __hash__(self) -> int:
        return hash((self.production, self.dot, self.input_position))

    def __str__(self) -> str:
        lhs = self.production.lhs
        matched = " ".join(self.production.rhs[:self.dot])
        remaining = " ".join(self.production.rhs[self.dot:])
        return f"{lhs} ::= {matched} . {remaining} ({self.input_position})"


def _closure(grammar: Grammar, items: set[Item], index: int) -> set[Item]:
    """
    Computes the closure of a set of items for an Earley state.

    Handles both prediction (add items for non-terminals after the dot) and
    nullable completion (immediately advance items whose next symbol can derive ε
    within this same state).  The two interact: predicting an ε-production makes
    its LHS nullable, which then advances any already-predicted item that had that
    LHS after its dot; conversely, any item added later with a already-nullable LHS
    after its dot is advanced immediately via the nullable shortcut.
    """
    seen: set[tuple[Production, int, int]] = {
        (it.production, it.dot, it.input_position) for it in items
    }
    result = list(items)
    # Maps lhs → the ε-item that completed it within this state, so we can set
    # completed_by on items advanced via the nullable shortcut.
    nullable_completions: dict[str, Item] = {}

    i = 0
    while i < len(result):
        item = result[i]
        i += 1

        if item.is_completed():
            # Only nullable completions predicted within this state contribute:
            # items carried in from scanning have input_position < index.
            if item.input_position != index:
                continue
            lhs = item.production.lhs
            if lhs in nullable_completions:
                continue
            nullable_completions[lhs] = item
            # Advance every item already in the state that was waiting for lhs.
            for other in list(result):
                if not other.is_completed() and other.get_next_symbol() == lhs:
                    key = (other.production, other.dot + 1, other.input_position)
                    if key not in seen:
                        seen.add(key)
                        new_item = Item(other.production, other.dot + 1, other.input_position)
                        new_item.prev_step = other
                        new_item.completed_by = item
                        result.append(new_item)
        else:
            next_sym = item.get_next_symbol()
            if next_sym not in grammar.non_terminals:
                continue
            # Prediction
            for production in grammar.lookup_productions(next_sym):
                key = (production, 0, index)
                if key not in seen:
                    seen.add(key)
                    result.append(Item(production, 0, index))
            # Nullable shortcut: if next_sym was already completed as nullable,
            # advance this item immediately without waiting for the completion step.
            if next_sym in nullable_completions:
                key = (item.production, item.dot + 1, item.input_position)
                if key not in seen:
                    seen.add(key)
                    new_item = Item(item.production, item.dot + 1, item.input_position)
                    new_item.prev_step = item
                    new_item.completed_by = nullable_completions[next_sym]
                    result.append(new_item)

    return set(result)