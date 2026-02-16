"""JSON serialization helpers for ARSNoP domain objects."""

from __future__ import annotations

from typing import Any

from arsnop.grammar import Production
from arsnop.lexer import Token
from arsnop.parser.ast import AST
from arsnop.parser.shift_reduce.state import Item, State
from arsnop.parser.shift_reduce.types import Action, ActionTable, GotoTable


def serialize_production(prod: Production) -> dict[str, Any]:
    return {"lhs": prod.lhs, "rhs": prod.rhs}


def serialize_item(item: Item) -> dict[str, Any]:
    return {
        "production": serialize_production(item.production),
        "dot": item.dot,
        "lookahead": sorted(item.lookahead),
    }


def serialize_state(index: int, state: State) -> dict[str, Any]:
    return {
        "index": index,
        "items": [serialize_item(it) for it in sorted(
            state.items,
            key=lambda i: (i.production.lhs, i.production.rhs, i.dot),
        )],
    }


def serialize_action(action: Action) -> dict[str, Any]:
    if action[0] == "shift":
        return {"type": "shift", "state": action[1]}
    elif action[0] == "reduce":
        return {"type": "reduce", "production": serialize_production(action[1])}
    else:
        return {"type": "accept"}


def serialize_action_table(table: ActionTable) -> dict[str, dict[str, Any]]:
    """Convert tuple-keyed action table to nested dict {state: {terminal: action}}."""
    result: dict[str, dict[str, Any]] = {}
    for (state, terminal), action in sorted(table.items()):
        state_key = str(state)
        if state_key not in result:
            result[state_key] = {}
        result[state_key][terminal] = serialize_action(action)
    return result


def serialize_goto_table(table: GotoTable) -> dict[str, dict[str, int]]:
    """Convert tuple-keyed goto table to nested dict {state: {non_terminal: next_state}}."""
    result: dict[str, dict[str, int]] = {}
    for (state, symbol), next_state in sorted(table.items()):
        state_key = str(state)
        if state_key not in result:
            result[state_key] = {}
        result[state_key][symbol] = next_state
    return result


def serialize_token(token: Token) -> dict[str, str]:
    return {"token": token.token, "lexeme": token.lexeme}


def serialize_ast(node: AST) -> dict[str, Any]:
    if node.children:
        return {
            "type": "node",
            "symbol": str(node.content),
            "children": [serialize_ast(child) for child in node.children],
        }
    else:
        content = node.content
        if isinstance(content, Token):
            return {
                "type": "token",
                "token": content.token,
                "lexeme": content.lexeme,
            }
        return {
            "type": "token",
            "token": str(content),
            "lexeme": str(content),
        }
