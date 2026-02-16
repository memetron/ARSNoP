"""Trace-generating Earley parser that records the operation (init/predict/scan/complete) on each item."""

from __future__ import annotations

from typing import Any

from src.grammar import Grammar, Production
from src.lexer import Token
from src.parser.ast import AST
from .serializers import serialize_production, serialize_token, serialize_ast


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


def traced_earley_parse(
    grammar: Grammar,
    tokens: list[Token],
    start_symbol: str = "start",
) -> dict[str, Any]:
    """Run the Earley algorithm and return the full chart with operation labels."""
    start_productions = grammar.lookup_productions(start_symbol)

    # Column 0: init items + predict closure
    init_items = [
        _TracedItem(p, 0, 0, "init") for p in start_productions
    ]
    col0_items = _predict_closure(grammar, init_items, 0)
    chart: list[list[_TracedItem]] = [col0_items]

    for i, tok in enumerate(tokens):
        col_index = i + 1
        # Scan from previous column
        scanned = _scan(chart[i], tok)
        if not scanned:
            return _build_result(tokens, chart, error=f"Unexpected token '{tok.lexeme}' ({tok.token}) at position {i}")
        # Complete + predict closure
        completed = _complete_and_predict(grammar, scanned, chart, col_index)
        chart.append(completed)

    # Look for a completed start item in the last column
    ast = _find_and_build_ast(chart, start_symbol)
    if ast is None:
        return _build_result(tokens, chart, error="Input not recognized by the grammar.")
    return _build_result(tokens, chart, ast=ast)


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
            # Complete: advance items in the origin column waiting for this LHS
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
            # Predict: if next symbol is a non-terminal, add its productions
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
            return _to_ast(item)
    return None


def _to_ast(item: _TracedItem) -> AST:
    """Convert a completed traced item into an AST (mirrors earley._to_ast)."""
    raw_items: list[_TracedItem] = []
    curr: _TracedItem = item
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


def _serialize_earley_item(item: _TracedItem) -> dict[str, Any]:
    return {
        "production": serialize_production(item.production),
        "dot": item.dot,
        "origin": item.origin,
        "operation": item.operation,
    }


def _build_result(
    tokens: list[Token],
    chart: list[list[_TracedItem]],
    ast: AST | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    serialized_chart: list[dict[str, Any]] = []
    for col_idx, col in enumerate(chart):
        token_at_col: dict[str, str] | None = None
        if col_idx > 0 and col_idx <= len(tokens):
            token_at_col = serialize_token(tokens[col_idx - 1])
        serialized_chart.append({
            "index": col_idx,
            "token": token_at_col,
            "items": [_serialize_earley_item(it) for it in col],
        })
    result: dict[str, Any] = {
        "tokens": [serialize_token(t) for t in tokens],
        "chart": serialized_chart,
        "ast": serialize_ast(ast) if ast else None,
    }
    if error is not None:
        result["error"] = error
    return result
