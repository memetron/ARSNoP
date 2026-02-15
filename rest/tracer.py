"""Trace-generating parse loop that mirrors Automaton.parse() but records each step."""

from __future__ import annotations

import copy
from typing import Any

from src.lexer import Token
from src.parser.ast import AST
from src.parser.shift_reduce.types import ActionTable, GotoTable, Action
from .serializers import serialize_production, serialize_token, serialize_ast


def traced_parse(
    action_table: ActionTable,
    goto_table: GotoTable,
    tokens: list[Token],
) -> dict[str, Any]:
    """Run shift-reduce parsing and return tokens, trace steps, and the AST."""
    buffer = tokens + [Token("$", "$")]
    stack: list[int] = [0]
    tree_stack: list[AST] = []
    index = 0
    steps: list[dict[str, Any]] = []
    step_num = 0

    while index < len(buffer):
        state = stack[-1]
        curr_token = buffer[index]

        try:
            action: Action = action_table[state, curr_token.token]
        except KeyError:
            return {
                "tokens": [serialize_token(t) for t in tokens],
                "trace": steps,
                "ast": None,
                "error": f"Unexpected token '{curr_token.lexeme}' ({curr_token.token}) at position {index}",
            }

        step_record: dict[str, Any] = {
            "step": step_num,
            "stack": list(stack),
            "inputBuffer": [serialize_token(t) for t in buffer[index:]],
            "action": _describe_action(action),
        }
        steps.append(step_record)
        step_num += 1

        if action[0] == "shift":
            tree_stack.append(AST(curr_token))
            stack.append(action[1])
            index += 1
        elif action[0] == "reduce":
            prod = action[1]
            children: list[AST] = []
            for _ in prod.rhs:
                stack.pop()
                children.append(tree_stack.pop())
            tree_stack.append(AST(prod.lhs, list(reversed(copy.deepcopy(children)))))
            stack.append(goto_table[(stack[-1], prod.lhs)])
        elif action[0] == "accept":
            ast = tree_stack[0] if tree_stack else None
            return {
                "tokens": [serialize_token(t) for t in tokens],
                "trace": steps,
                "ast": serialize_ast(ast) if ast else None,
            }

    return {
        "tokens": [serialize_token(t) for t in tokens],
        "trace": steps,
        "ast": None,
        "error": "Unexpected end of input",
    }


def _describe_action(action: Action) -> dict[str, Any]:
    if action[0] == "shift":
        return {"type": "shift", "state": action[1]}
    elif action[0] == "reduce":
        return {
            "type": "reduce",
            "production": serialize_production(action[1]),
        }
    else:
        return {"type": "accept"}
