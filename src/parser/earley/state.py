from __future__ import annotations

from src.grammar.grammar import Grammar
from src.grammar.production import Production
from src.lexer.token import Token


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
        new_items = set()
        for item in self.items:
            if not item.is_completed() and item.get_next_symbol() == symbol:
                new_item = Item(item.production, item.dot + 1, item.input_position)
                new_item.prev_step = item
                new_item.matched_token = matched_by
                new_items.add(new_item)
        return new_items

    def __str__(self):
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

    def __eq__(self, other):
        return (
            isinstance(other, Item) and
            self.production == other.production and
            self.dot == other.dot and
            self.input_position == other.input_position
        )

    def __hash__(self):
        return hash((self.production, self.dot, self.input_position))

    def __str__(self):
        lhs = self.production.lhs
        matched = " ".join(self.production.rhs[:self.dot])
        remaining = " ".join(self.production.rhs[self.dot:])
        return f"{lhs} ::= {matched} . {remaining} ({self.input_position})"


def _closure(grammar: Grammar, items: set[Item], index: int) -> set[Item]:
    """
    Computes the closure of a set of items over a grammar.
    Args:
        grammar (Grammar): The grammar to use for closure computation.
        items (set[Item]): The initial set of items.
        index (int): The index for newly created items.
    Returns:
        set[Item]: The augmented set of items.
    """
    new_items = list(items)
    for item in new_items:
        if not item.is_completed():
            next_symbol = item.get_next_symbol()
            if next_symbol in grammar.non_terminals:
                for production in grammar.lookup_productions(next_symbol):
                    new_item = Item(production, 0, index)
                    if new_item not in new_items:
                        new_items.append(new_item)
    return set(new_items)