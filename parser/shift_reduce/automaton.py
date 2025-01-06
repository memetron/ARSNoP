import copy
from typing import Iterator

from lexer.token import Token
from parser.ast import AST
from parser.parsingEngine import ParsingEngine


class Automaton(ParsingEngine):
    """
    A shift-reduce automaton that processes a stream of tokens to construct an AST.

    Methods:
        process(symbols: List[Token]) -> AST:
            Processes a list of tokens, applying shift-reduce parsing, and returns the resulting AST.
    """

    def __init__(self, goto, action):
        """
        Initializes the Automaton with goto and action tables.

        Args:
            goto (dict): The goto table, mapping (state, symbol) to the next state.
            action (dict): The action table, mapping (state, token) to an action.
        """
        self._goto = goto
        self._action = action

    def parse(self, symbols: Iterator[Token]) -> AST:
        """
        Processes a stream of symbols (tokens) using shift-reduce parsing to construct an AST.
        Args:
            symbols (List[Token]): A list of tokens to parse.
        Returns:
            AST: The resulting abstract syntax tree after parsing the input symbols.
        Raises:
            KeyError: If an unexpected token is encountered or an invalid action is specified.
        """

        buffer = symbols + [Token("$", "$")]
        stack = [0]
        tree_stack = []
        index = 0

        while index < len(buffer):
            state = stack[-1]
            curr_token = buffer[index]
            action = self._action[state, curr_token.token]

            if action[0] == "shift":
                # Perform a shift action - and keep track of the shifted token on the ast
                tree_stack.append(AST(curr_token))
                stack.append(action[1])
                index += 1
            elif action[0] == "reduce":
                # reduce by popping |rhs| symbols from the stack and merge an equivalent number of ast nodes
                prod = action[1]
                children = []
                for _ in prod.rhs:
                    stack.pop()
                    children.append(tree_stack.pop())
                tree_stack.append(AST(prod.lhs, list(reversed(copy.deepcopy(children)))))
                stack.append(self._goto[(stack[-1], prod.lhs)])
            elif action[0] == "accept":
                return tree_stack[0]
