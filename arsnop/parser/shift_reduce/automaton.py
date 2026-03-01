import copy

from ...grammar.bnf_types import InlineType
from ...lexer import Lexer, Token
from ...ast import AST
from ..parsingEngine import ParsingEngine
from ..tree import TreeItem, make_tree_item, splice_children
from .trace import ShiftReduceTrace, TraceAction, TraceStep
from .types import GotoTable, ActionTable, Action


class Automaton(ParsingEngine):
    """A shift-reduce automaton that processes a stream of tokens to construct an AST."""

    def __init__(self, goto: GotoTable, action: ActionTable) -> None:
        self._goto = goto
        self._action = action
        self._valid_by_state: dict[int, frozenset[str]] = {}
        for state, terminal in action.keys():
            self._valid_by_state[state] = self._valid_by_state.get(state, frozenset()) | {terminal}

    def parse(self, text: str, lexer: Lexer) -> AST:
        """Parse with contextual lexing, consulting the action table at each step."""
        result = self.trace(text, lexer)
        if result.error is not None:
            raise ValueError(result.error)
        assert result.ast is not None
        return result.ast

    def trace(self, text: str, lexer: Lexer) -> ShiftReduceTrace:
        """Shift-reduce parse loop that fetches tokens on demand via lex_one."""
        stack: list[int] = [0]
        tree_stack: list[TreeItem] = []
        steps: list[TraceStep] = []
        tokens: list[Token] = []
        pos = 0
        lex_error: list[str] = []

        def advance() -> Token | None:
            """Fetch the next token from the input."""
            nonlocal pos
            valid = self._valid_by_state.get(stack[-1], frozenset()) - {"$"}
            try:
                tok, pos = lexer.lex_one(text, pos, valid)
                return tok
            except Exception as e:
                lex_error.append(str(e))
                return None

        _next = advance()
        if lex_error:
            return ShiftReduceTrace(tokens=(), steps=(), ast=None, error=lex_error[0])
        lookahead = _next if _next is not None else Token("$", "$")

        while True:
            state = stack[-1]

            try:
                action: Action = self._action[state, lookahead.token]
            except KeyError:
                return ShiftReduceTrace(
                    tokens=tuple(tokens),
                    steps=tuple(steps),
                    ast=None,
                    error=f"Unexpected token '{lookahead.lexeme}' ({lookahead.token})",
                )

            steps.append(TraceStep(
                step=len(steps),
                stack=tuple(stack),
                input_buffer=(lookahead,),
                action=_to_trace_action(action),
            ))

            if action[0] == "shift":
                tokens.append(lookahead)
                tree_stack.append([] if lookahead.inline else AST(lookahead))
                stack.append(action[1])
                _next = advance()
                if lex_error:
                    return ShiftReduceTrace(tokens=tuple(tokens), steps=tuple(steps), ast=None, error=lex_error[0])
                lookahead = _next if _next is not None else Token("$", "$")
            elif action[0] == "reduce":
                prod = action[1]
                raw: list[TreeItem] = []
                for _ in prod.rhs:
                    stack.pop()
                    raw.append(tree_stack.pop())
                children = splice_children(reversed(raw))
                label = prod.label if prod.label is not None else prod.lhs
                tree_stack.append(make_tree_item(label, prod.inline if prod.label is None else InlineType.NONE, copy.deepcopy(children)))
                stack.append(self._goto[(stack[-1], prod.lhs)])
            elif action[0] == "accept":
                top = tree_stack[0] if tree_stack else None
                ast = top if isinstance(top, AST) else None
                return ShiftReduceTrace(
                    tokens=tuple(tokens),
                    steps=tuple(steps),
                    ast=ast,
                )


def _to_trace_action(action: Action) -> TraceAction:
    """Convert an Action tuple to a TraceAction dataclass."""
    if action[0] == "shift":
        return TraceAction(type="shift", state=action[1])
    elif action[0] == "reduce":
        return TraceAction(type="reduce", production=action[1])
    else:
        return TraceAction(type="accept")
