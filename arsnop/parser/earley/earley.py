from __future__ import annotations

from collections.abc import Callable

from ...grammar.grammar import Grammar
from ...grammar.production import Production
from ...lexer import Token
from ...ast import AST
from ..tree import TreeItem, make_tree_item, splice_children
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
        prev_columns = [list(s.items) for s in self._states]
        column = _build_column(self._grammar, seed, prev_columns, new_index)
        self._states.append(State(self._grammar, set(column), new_index))

    def _get_recognized_item(self) -> Item | None:
        """
        Checks if the input string is recognized by the grammar.

        Returns:
            Item | None: The recognized item if found, otherwise None.
        """
        for item in self._states[-1].items:
            if (item.is_completed()
                    and item.input_position == 0
                    and item.production.lhs == self._grammar.start_symbol):
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
    seed: set[Item] | list[Item],
    prev_columns: list[list[Item]],
    index: int,
    *,
    predict_op: str | None = None,
    complete_op: str | None = None,
) -> list[Item]:
    """Build one Earley column via a predict+complete fixpoint.

    Items are deduplicated by (production, dot, input_position); the first
    derivation found wins.
    """
    seen: set[tuple[Production, int, int]] = set()
    result: list[Item] = []
    nullable_completions: dict[str, Item] = {}

    def add(item: Item) -> bool:
        key = (item.production, item.dot, item.input_position)
        if key not in seen:
            seen.add(key)
            result.append(item)
            return True
        return False

    for item in seed:
        add(item)

    i = 0
    while i < len(result):
        item = result[i]
        i += 1
        if item.is_completed():
            _complete(item, result, nullable_completions, prev_columns, index, add, complete_op)
        else:
            _predict(item, grammar, nullable_completions, index, add, predict_op, complete_op)

    return result


def _complete(
    item: Item,
    result: list[Item],
    nullable_completions: dict[str, Item],
    prev_columns: list[list[Item]],
    index: int,
    add: Callable[[Item], bool],
    complete_op: str | None = None,
) -> None:
    """Advance items that were waiting for this completed non-terminal."""
    lhs = item.production.lhs
    origin = item.input_position
    if origin == index:
        _complete_nullable(item, lhs, result, nullable_completions, add, complete_op)
    else:
        _complete_nonnullable(item, lhs, origin, prev_columns, add, complete_op)


def _complete_nullable(
    item: Item,
    lhs: str,
    result: list[Item],
    nullable_completions: dict[str, Item],
    add: Callable[[Item], bool],
    complete_op: str | None = None,
) -> None:
    """Record an ε-completion and retroactively advance items already in the column."""
    if lhs in nullable_completions:
        return
    nullable_completions[lhs] = item
    for other in list(result):
        if not other.is_completed() and other.get_next_symbol() == lhs:
            new_item = Item(other.production, other.dot + 1, other.input_position, complete_op)
            new_item.prev_step = other
            new_item.completed_by = item
            add(new_item)


def _complete_nonnullable(
    item: Item,
    lhs: str,
    origin: int,
    prev_columns: list[list[Item]],
    add: Callable[[Item], bool],
    complete_op: str | None = None,
) -> None:
    """Advance items from the origin column that were waiting on lhs."""
    for origin_item in prev_columns[origin]:
        if not origin_item.is_completed() and origin_item.get_next_symbol() == lhs:
            new_item = Item(origin_item.production, origin_item.dot + 1, origin_item.input_position, complete_op)
            new_item.prev_step = origin_item
            new_item.completed_by = item
            add(new_item)


def _predict(
    item: Item,
    grammar: Grammar,
    nullable_completions: dict[str, Item],
    index: int,
    add: Callable[[Item], bool],
    predict_op: str | None = None,
    complete_op: str | None = None,
) -> None:
    """Predict items for the next non-terminal, applying any nullable shortcuts."""
    next_sym = item.get_next_symbol()
    if next_sym not in grammar.non_terminals:
        return
    for prod in grammar.lookup_productions(next_sym):
        add(Item(prod, 0, index, predict_op))
    if next_sym in nullable_completions:
        new_item = Item(item.production, item.dot + 1, item.input_position, complete_op)
        new_item.prev_step = item
        new_item.completed_by = nullable_completions[next_sym]
        add(new_item)


def _to_ast(item: Item) -> AST:
    """Convert a completed item to an AST, splicing out any modifier-generated nodes."""
    result = _to_tree_item(item)
    assert isinstance(result, AST)
    return result


def _to_tree_item(item: Item) -> TreeItem:
    """Recursively build an AST node or an inline list for modifier rules.

    Non-modifier items return an ``AST`` node as usual.  Modifier items return
    a bare ``list[AST]`` so their children are spliced directly into the
    parent's child list, leaving no wrapper node in the final tree.
    """
    raw_items: list[Item] = []
    curr: Item = item
    while curr.prev_step:
        raw_items.append(curr)
        curr = curr.prev_step
    tree_items: list[TreeItem] = []
    for curr_item in raw_items:
        if curr_item.completed_by is not None:
            tree_items.append(_to_tree_item(curr_item.completed_by))
        elif curr_item.matched_token is not None:
            tree_items.append(AST(curr_item.matched_token))
    ordered = splice_children(reversed(tree_items))
    return make_tree_item(item.production.lhs, item.production.modifier, ordered)


def _traced_earley_parse(
    grammar: Grammar,
    tokens: list[Token],
    start_symbol: str = "start",
) -> EarleyTrace:
    """Run the Earley algorithm and return an EarleyTrace with operation labels."""
    start_productions = grammar.lookup_productions(start_symbol)
    init_items = [Item(p, 0, 0, "init") for p in start_productions]
    chart: list[list[Item]] = [
        _build_column(grammar, init_items, [], 0, predict_op="predict", complete_op="complete")
    ]

    for i, tok in enumerate(tokens):
        col_index = i + 1
        scanned = _scan(chart[i], tok)
        if not scanned:
            return _build_earley_trace(
                tokens,
                chart,
                error=f"Unexpected token '{tok.lexeme}' ({tok.token}) at position {i}",
            )
        col = _build_column(
            grammar, scanned, chart, col_index,
            predict_op="predict", complete_op="complete",
        )
        chart.append(col)

    ast = _find_and_build_ast(chart, start_symbol)
    if ast is None:
        return _build_earley_trace(
            tokens, chart, error="Input not recognized by the grammar.",
        )
    return _build_earley_trace(tokens, chart, ast=ast)


def _scan(
    prev_col: list[Item],
    tok: Token,
) -> list[Item]:
    """Advance items whose next symbol matches the token."""
    scanned: list[Item] = []
    for item in prev_col:
        if item.is_completed():
            continue
        if item.get_next_symbol() == tok.token:
            new_item = Item(item.production, item.dot + 1, item.input_position, "scan")
            new_item.prev_step = item
            new_item.matched_token = tok
            scanned.append(new_item)
    return scanned


def _find_and_build_ast(
    chart: list[list[Item]],
    start_symbol: str,
) -> AST | None:
    """Find a completed start item in the last column and reconstruct the AST."""
    if not chart:
        return None
    for item in chart[-1]:
        if item.is_completed() and item.input_position == 0 and item.production.lhs == start_symbol:
            return _to_ast(item)
    return None


def _build_earley_trace(
    tokens: list[Token],
    chart: list[list[Item]],
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
                    origin=it.input_position,
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
