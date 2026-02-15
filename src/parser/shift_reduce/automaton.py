import copy

from ...lexer import Token
from ..ast import AST
from ..parsingEngine import ParsingEngine
from .types import GotoTable, ActionTable, Action


class Automaton(ParsingEngine):
    """
    A shift-reduce automaton that processes a stream of tokens to construct an AST.

    Methods:
        process(symbols: List[Token]) -> AST:
            Processes a list of tokens, applying shift-reduce parsing, and returns the resulting AST.
    """

    def __init__(self, goto: GotoTable, action: ActionTable) -> None:
        """
        Initializes the Automaton with goto and action tables.

        Args:
            goto (dict): The goto table, mapping (state, symbol) to the next state.
            action (dict): The action table, mapping (state, token) to an action.
        """
        self._goto = goto
        self._action = action

    def parse(self, stream: list[Token]) -> AST:
        """
        Processes a stream of symbols (tokens) using shift-reduce parsing to construct an AST.
        Args:
            stream (list[Token]): A list of tokens to parse.
        Returns:
            AST: The resulting abstract syntax tree after parsing the input symbols.
        Raises:
            KeyError: If an unexpected token is encountered or an invalid action is specified.
        """

        buffer = stream + [Token("$", "$")]
        stack: list[int] = [0]
        tree_stack: list[AST] = []
        index = 0

        while index < len(buffer):
            state = stack[-1]
            curr_token = buffer[index]
            action: Action = self._action[state, curr_token.token]

            if action[0] == "shift":
                # Perform a shift action - and keep track of the shifted token on the ast
                tree_stack.append(AST(curr_token))
                stack.append(action[1])
                index += 1
            elif action[0] == "reduce":
                # reduce by popping |rhs| symbols from the stack and merge an equivalent number of ast nodes
                prod = action[1]
                children: list[AST] = []
                for _ in prod.rhs:
                    stack.pop()
                    children.append(tree_stack.pop())
                tree_stack.append(AST(prod.lhs, list(reversed(copy.deepcopy(children)))))
                stack.append(self._goto[(stack[-1], prod.lhs)])
            elif action[0] == "accept":
                return tree_stack[0]

        raise ValueError("Unexpected end of input")
