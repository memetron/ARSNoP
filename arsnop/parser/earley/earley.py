from __future__ import annotations

from ...grammar.grammar import Grammar
from ...grammar.production import Production
from ...lexer import Token
from ...ast import AST
from .state import Item, State
from .trace import EarleyColumn, EarleyTrace, TracedEarleyItem
from ..parsingEngine import ParsingEngine


class Earley(ParsingEngine):
    """
    Implements the Earley parsing algorithm.
    """
    def __init__(self, grammar: Grammar):
        """
        Initializes the Earley parser.
        Args:
            grammar (Grammar): The grammar for parsing.
            start_symbol (str): The start symbol of the grammar.
        """
        self._grammar = grammar
        start_productions = grammar.lookup_productions(grammar.start_symbol)
        start_items = {Item(production, 0, 0) for production in start_productions}
        self._states = [State(grammar, start_items, 0)]

    def read(self, symbol: Token) -> None:
        """
        Processes a symbol from the input and advances the parser state.
        Args:
            symbol (Token): The input symbol to read.
        """
        seed = self._states[-1].successor(symbol.token, matched_by=symbol)
        new_index = len(self._states)
        column = _build_column(self._grammar, seed, self._states, new_index)
        self._states.append(State(self._grammar, set(column), new_index))

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

    @classmethod
    def trace(
        cls,
        grammar: Grammar,
        tokens: list[Token],
        start_symbol: str = "start",
    ) -> EarleyTrace:
        """Run the Earley algorithm and return the full chart with operation labels."""
        return _traced_earley_parse(grammar, tokens, start_symbol)


def _build_column(
    grammar: Grammar,
    seed: set[Item],
    prev_states: list[State],
    index: int,
) -> list[Item]:
    """Build one Earley column via a predict+complete fixpoint.

    Handles both nullable completions (origin == index, resolved within this
    column) and non-nullable completions (origin < index, resolved by looking up
    the appropriate previous state).  Items are deduplicated by
    (production, dot, input_position); the first derivation found wins.
    """
    seen: set[tuple[Production, int, int]] = set()
    result: list[Item] = []
    # Maps lhs → the ε-item that completed it within this column.
    nullable_completions: dict[str, Item] = {}

    def _add(item: Item) -> bool:
        key = (item.production, item.dot, item.input_position)
        if key not in seen:
            seen.add(key)
            result.append(item)
            return True
        return False

    for item in seed:
        _add(item)

    i = 0
    while i < len(result):
        item = result[i]
        i += 1

        if item.is_completed():
            lhs = item.production.lhs
            origin = item.input_position
            if origin == index:
                # Nullable completion within this column.
                if lhs not in nullable_completions:
                    nullable_completions[lhs] = item
                    for other in list(result):
                        if not other.is_completed() and other.get_next_symbol() == lhs:
                            new_item = Item(other.production, other.dot + 1, other.input_position)
                            new_item.prev_step = other
                            new_item.completed_by = item
                            _add(new_item)
            else:
                # Non-nullable completion: advance items from the origin state.
                for origin_item in prev_states[origin].items:
                    if not origin_item.is_completed() and origin_item.get_next_symbol() == lhs:
                        new_item = Item(origin_item.production, origin_item.dot + 1, origin_item.input_position)
                        new_item.prev_step = origin_item
                        new_item.completed_by = item
                        _add(new_item)
        else:
            next_sym = item.get_next_symbol()
            if next_sym not in grammar.non_terminals:
                continue
            # Prediction: add items for each production of next_sym.
            for prod in grammar.lookup_productions(next_sym):
                _add(Item(prod, 0, index))
            # Nullable shortcut: if next_sym was already ε-completed in this
            # column, immediately advance past it.
            if next_sym in nullable_completions:
                new_item = Item(item.production, item.dot + 1, item.input_position)
                new_item.prev_step = item
                new_item.completed_by = nullable_completions[next_sym]
                _add(new_item)

    return result


def _to_ast(item: Item) -> AST:
    """
    Converts a recognized item to an abstract syntax tree.
    Args:
        item (Item): The recognized item.
    Returns:
        AST: The constructed abstract syntax tree.
    """
    raw_items: list[Item] = []
    curr: Item = item
    while curr.prev_step:
        raw_items.append(curr)
        curr = curr.prev_step
    children: list[AST] = []
    for curr_item in raw_items:
        if curr_item.completed_by is not None:
            children.append(_to_ast(curr_item.completed_by))
        elif curr_item.matched_token is not None:
            children.append(AST(curr_item.matched_token))
    return AST(item.production.lhs, list(reversed(children)))


# --- Traced Earley internals ---


class _TracedItem:
    """An Earley item annotated with the operation that created it."""

    __slots__ = (
        "production",
        "dot",
        "origin",
        "operation",
        "prev_step",
        "matched_token",
        "completed_by",
    )

    def __init__(
        self,
        production: Production,
        dot: int,
        origin: int,
        operation: str,
    ) -> None:
        self.production = production
        self.dot = dot
        self.origin = origin
        self.operation = operation
        self.prev_step: _TracedItem | None = None
        self.matched_token: Token | None = None
        self.completed_by: _TracedItem | None = None

    def is_completed(self) -> bool:
        return self.dot == len(self.production.rhs)

    def next_symbol(self) -> str:
        return self.production.rhs[self.dot]

    def key(self) -> tuple[Production, int, int]:
        return (self.production, self.dot, self.origin)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _TracedItem):
            return False
        return self.key() == other.key()

    def __hash__(self) -> int:
        return hash(self.key())


def _traced_earley_parse(
    grammar: Grammar,
    tokens: list[Token],
    start_symbol: str = "start",
) -> EarleyTrace:
    """Run the Earley algorithm and return an EarleyTrace with operation labels."""
    start_productions = grammar.lookup_productions(start_symbol)

    init_items = [_TracedItem(p, 0, 0, "init") for p in start_productions]
    col0_items = _predict_closure(grammar, init_items, 0)
    chart: list[list[_TracedItem]] = [col0_items]

    for i, tok in enumerate(tokens):
        col_index = i + 1
        scanned = _scan(chart[i], tok)
        if not scanned:
            return _build_earley_trace(
                tokens,
                chart,
                error=f"Unexpected token '{tok.lexeme}' ({tok.token}) at position {i}",
            )
        completed = _complete_and_predict(grammar, scanned, chart, col_index)
        chart.append(completed)

    ast = _find_and_build_ast(chart, start_symbol)
    if ast is None:
        return _build_earley_trace(
            tokens, chart, error="Input not recognized by the grammar.",
        )
    return _build_earley_trace(tokens, chart, ast=ast)


def _predict_closure(
    grammar: Grammar,
    items: list[_TracedItem],
    col_index: int,
) -> list[_TracedItem]:
    """Add predicted items for non-terminals after the dot."""
    seen: set[tuple[Production, int, int]] = {it.key() for it in items}
    result = list(items)
    for item in result:
        if item.is_completed():
            continue
        sym = item.next_symbol()
        if sym not in grammar.non_terminals:
            continue
        for prod in grammar.lookup_productions(sym):
            key = (prod, 0, col_index)
            if key not in seen:
                seen.add(key)
                result.append(_TracedItem(prod, 0, col_index, "predict"))
    return result


def _scan(
    prev_col: list[_TracedItem],
    tok: Token,
) -> list[_TracedItem]:
    """Advance items whose next symbol matches the token."""
    scanned: list[_TracedItem] = []
    for item in prev_col:
        if item.is_completed():
            continue
        if item.next_symbol() == tok.token:
            new_item = _TracedItem(item.production, item.dot + 1, item.origin, "scan")
            new_item.prev_step = item
            new_item.matched_token = tok
            scanned.append(new_item)
    return scanned


def _complete_and_predict(
    grammar: Grammar,
    scanned: list[_TracedItem],
    chart: list[list[_TracedItem]],
    col_index: int,
) -> list[_TracedItem]:
    """Run the complete-then-predict loop until no new items are added."""
    seen: set[tuple[Production, int, int]] = {it.key() for it in scanned}
    result = list(scanned)
    i = 0
    while i < len(result):
        item = result[i]
        i += 1
        if item.is_completed():
            lhs = item.production.lhs
            for origin_item in chart[item.origin]:
                if origin_item.is_completed():
                    continue
                if origin_item.next_symbol() == lhs:
                    key = (origin_item.production, origin_item.dot + 1, origin_item.origin)
                    if key not in seen:
                        seen.add(key)
                        new_item = _TracedItem(
                            origin_item.production,
                            origin_item.dot + 1,
                            origin_item.origin,
                            "complete",
                        )
                        new_item.prev_step = origin_item
                        new_item.completed_by = item
                        result.append(new_item)
        else:
            sym = item.next_symbol()
            if sym in grammar.non_terminals:
                for prod in grammar.lookup_productions(sym):
                    key = (prod, 0, col_index)
                    if key not in seen:
                        seen.add(key)
                        result.append(_TracedItem(prod, 0, col_index, "predict"))
    return result


def _find_and_build_ast(
    chart: list[list[_TracedItem]],
    start_symbol: str,
) -> AST | None:
    """Find a completed start item in the last column and reconstruct the AST."""
    if not chart:
        return None
    for item in chart[-1]:
        if item.is_completed() and item.origin == 0 and item.production.lhs == start_symbol:
            return _traced_to_ast(item)
    return None


def _traced_to_ast(item: _TracedItem) -> AST:
    """Convert a completed traced item into an AST."""
    raw_items: list[_TracedItem] = []
    curr: _TracedItem = item
    while curr.prev_step:
        raw_items.append(curr)
        curr = curr.prev_step
    children: list[AST] = []
    for curr_item in raw_items:
        if curr_item.completed_by is not None:
            children.append(_traced_to_ast(curr_item.completed_by))
        elif curr_item.matched_token is not None:
            children.append(AST(curr_item.matched_token))
    return AST(item.production.lhs, list(reversed(children)))


def _build_earley_trace(
    tokens: list[Token],
    chart: list[list[_TracedItem]],
    ast: AST | None = None,
    error: str | None = None,
) -> EarleyTrace:
    """Assemble an EarleyTrace from the raw chart."""
    columns: list[EarleyColumn] = []
    for col_idx, col in enumerate(chart):
        token_at_col = tokens[col_idx - 1] if 0 < col_idx <= len(tokens) else None
        columns.append(EarleyColumn(
            index=col_idx,
            token=token_at_col,
            items=tuple(
                TracedEarleyItem(
                    production=it.production,
                    dot=it.dot,
                    origin=it.origin,
                    operation=it.operation,  # type: ignore[arg-type]
                )
                for it in col
            ),
        ))
    return EarleyTrace(
        tokens=tuple(tokens),
        chart=tuple(columns),
        ast=ast,
        error=error,
    )