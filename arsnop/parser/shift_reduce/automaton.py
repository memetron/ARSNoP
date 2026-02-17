from ...grammar import Production
from ...lexer import Token
from ..ast import AST
from ..parsingEngine import ParsingEngine
from .trace import ShiftReduceTrace, TraceAction, TraceStep
from .types import GotoTable, ActionTable, Action


class Automaton(ParsingEngine):
    """A shift-reduce automaton that processes a stream of tokens to construct an AST."""

    def __init__(self, goto: GotoTable, action: ActionTable) -> None:
        self._goto = goto
        self._action = action

    def parse(self, stream: list[Token]) -> AST:
        """Parse a token stream and return the AST, or raise on error."""
        result = self.trace(stream)
        if result.error is not None:
            raise ValueError(result.error)
        assert result.ast is not None
        return result.ast

    def trace(self, stream: list[Token]) -> ShiftReduceTrace:
        """Run shift-reduce parsing and record each step as a TraceStep."""
        buffer = stream + [Token("$", "$")]
        stack: list[int] = [0]
        tree_stack: list[AST] = []
        index = 0
        steps: list[TraceStep] = []

        while index < len(buffer):
            state = stack[-1]
            curr_token = buffer[index]

            try:
                action: Action = self._action[state, curr_token.token]
            except KeyError:
                return ShiftReduceTrace(
                    tokens=tuple(stream),
                    steps=tuple(steps),
                    ast=None,
                    error=f"Unexpected token '{curr_token.lexeme}' ({curr_token.token}) at position {index}",
                )

            steps.append(TraceStep(
                step=len(steps),
                stack=tuple(stack),
                input_buffer=tuple(buffer[index:]),
                action=TraceAction.from_action(action),
            ))

            if action[0] == "shift":
                tree_stack.append(AST(curr_token))
                stack.append(action[1])
                index += 1
            elif action[0] == "reduce":
                self._reduce(action[1], stack, tree_stack)
            elif action[0] == "accept":
                return ShiftReduceTrace(
                    tokens=tuple(stream),
                    steps=tuple(steps),
                    ast=tree_stack[0] if tree_stack else None,
                )

        return ShiftReduceTrace(
            tokens=tuple(stream),
            steps=tuple(steps),
            ast=None,
            error="Unexpected end of input",
        )

    def _reduce(self, prod: Production, stack: list[int], tree_stack: list[AST]) -> None:
        """Pop RHS symbols off the stacks, push a new AST node, and goto."""
        children: list[AST] = []
        for _ in prod.rhs:
            stack.pop()
            children.append(tree_stack.pop())
        tree_stack.append(AST(prod.lhs, reversed(children)))
        stack.append(self._goto[(stack[-1], prod.lhs)])
