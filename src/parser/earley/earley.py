from ...grammar import Grammar
from ...lexer import Token
from ..ast import AST
from .state import Item, State
from ..parsingEngine import ParsingEngine


class Earley(ParsingEngine):
    """
    Implements the Earley parsing algorithm.
    """
    def __init__(self, grammar: Grammar, start_symbol: str = 'start'):
        """
        Initializes the Earley parser.
        Args:
            grammar (Grammar): The grammar for parsing.
            start_symbol (str): The start symbol of the grammar.
        """
        self._grammar = grammar
        start_productions = grammar.lookup_productions(start_symbol)
        start_items = {Item(production, 0, 0) for production in start_productions}
        self._states = [State(grammar, start_items, 0)]

    def read(self, symbol: Token):
        """
        Processes a symbol from the input and advances the parser state.
        Args:
            symbol (Token): The input symbol to read.
        """
        items = list(self._states[-1].successor(symbol.token, matched_by=symbol))
        for item in items:
            if item.is_completed():
                lhs = item.production.lhs
                input_position = item.input_position
                completed_items = self._states[input_position].successor(lhs)
                for completed_item in completed_items:
                    if completed_item not in items:
                        completed_item.completed_by = item
                        items.append(completed_item)
        self._states.append(State(self._grammar, set(items), len(self._states)))

    def _get_recognized_item(self) -> Item | None:
        """
        Checks if the input string is recognized by the grammar.

        Returns:
            Item | None: The recognized item if found, otherwise None.
        """
        for item in self._states[-1].items:
            if item.is_completed() and item.input_position == 0:
                return item
        return None

    def parse(self, stream: list[Token]) -> AST:
        """
        Parses a list of tokens.
        Args:
            stream (list[Token]): The input tokens to parse.
        Returns:
            AST: The abstract syntax tree for the input.
        """
        for token in stream:
            self.read(token)
        recognized_item = self._get_recognized_item()
        if recognized_item:
            return _to_ast(recognized_item)
        raise ValueError("Input not recognized by the grammar.")


def _to_ast(item: Item) -> AST:
    """
    Converts a recognized item to an abstract syntax tree.
    Args:
        item (Item): The recognized item.
    Returns:
        AST: The constructed abstract syntax tree.
    """
    items = []
    curr = item
    while curr.prev_step:
        items.append(curr)
        curr = curr.prev_step
    for i, curr in enumerate(items):
        if curr.completed_by is not None:
            items[i] = _to_ast(curr.completed_by)
        else:
            items[i] = AST(curr.matched_token)
    return AST(item.production.lhs, reversed(items))