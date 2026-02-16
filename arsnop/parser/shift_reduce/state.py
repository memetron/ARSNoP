from __future__ import annotations

from dataclasses import dataclass
from ...grammar import Production


@dataclass(frozen=True)
class Item:
    """
    Represents a single item in the parsing process.
    Attributes:
        production: The production associated with this item.
        dot: The position of the dot in the production's RHS.
        lookahead: The lookahead set for LR(1) items. Default is empty for LR(0).
    """

    production: Production
    dot: int
    lookahead: frozenset[str] = frozenset()

    def is_complete(self) -> bool:
        """Checks if the item is complete (dot at the end of the production)."""
        return self.dot == len(self.production.rhs)


@dataclass(frozen=True)
class State:
    """
    Represents a state in the parsing process.
    Attributes:
        items: A frozenset of items in this state.
    """

    items: frozenset[Item]

    def get_kernel(self) -> frozenset[tuple[Production, int]]:
        """Extracts the kernel (core items without lookahead) from the state."""
        return frozenset((item.production, item.dot) for item in self.items)
