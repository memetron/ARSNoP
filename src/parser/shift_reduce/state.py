from __future__ import annotations

from collections.abc import Iterable
from ...grammar import Production


class Item:
    """
    Represents a single item in the parsing process.
    Attributes:
        production (Production): The production associated with this item.
        dot (int): The position of the dot in the production's RHS.
        lookahead (frozenset): The lookahead set for LR(1) items. Default is empty for LR(0).
    """

    def __init__(self, production: Production, dot: int, lookahead: frozenset[str] = frozenset()) -> None:
        self.production = production
        self.dot = dot
        self.lookahead = lookahead

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Item):
            return NotImplemented
        return (
                self.production == other.production and
                self.dot == other.dot and
                self.lookahead == other.lookahead
        )

    def __hash__(self) -> int:
        return hash((self.production, self.dot, tuple(self.lookahead)))

    def __repr__(self) -> str:
        return f"Item({self.production}, dot={self.dot}, lookahead={{{', '.join(self.lookahead)}}})"


class State:
    """
    Represents a state in the parsing process.
    Attributes:
        items (set): A set of items in this state.
    """

    def __init__(self, items: Iterable[Item]) -> None:
        self.items: frozenset[Item] = frozenset(items)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, State):
            return NotImplemented
        return self.items == other.items

    def __hash__(self) -> int:
        return hash(self.items)

    def __repr__(self) -> str:
        return f"State({list(self.items)})"

    def get_kernel(self) -> frozenset[tuple[Production, int]]:
        """Extracts the kernel (core items without lookahead) from the state."""
        return frozenset((item.production, item.dot) for item in self.items)
