import re
from collections.abc import Sequence

from arsnop.grammar.bnf_types import TerminalSpec

from .token import Token


class Lexer:
    """
    A class for tokenizing input text into a sequence of tokens based on defined terminal rules.

    Attributes:
        terminals (dict): A dictionary mapping terminal names to their compiled regular expressions.
        ignored (list): A list of terminal names to ignore during tokenization.

    Methods:
        lex(text: str) -> List[Token]:
            Tokenizes the input text based on the defined terminals and returns a list of tokens.
    """

    def __init__(self, terminals: Sequence[TerminalSpec], ignored: Sequence[str]) -> None:
        """
        Initializes the Lexer with structured terminal definitions.

        Args:
            terminals: A sequence of TerminalSpec objects (name + pattern).
            ignored: A sequence of terminal names to filter out during lexing.
        """
        self.terminals: dict[str, re.Pattern[str]] = {
            spec.name: re.compile(f"^{spec.pattern}") for spec in terminals
        }
        self.ignored: list[str] = list(ignored)

    def lex(self, text: str) -> list[Token]:
        """
        Tokenizes the input text based on the defined terminals.
        Args:
            text (str): The input text to tokenize.
        Returns:
            List[Token]: A list of `Token` objects representing the tokenized input.
        Raises:
            Exception: If no matching terminal is found for a portion of the input text.
        """
        pos = 0
        sequence: list[Token] = []
        line_number = 1
        column_number = 1

        while pos < len(text):
            longest = ""
            token = ""
            for terminal, regex in self.terminals.items():
                match = regex.match(text[pos:])
                if match:
                    if len(match.group()) > len(longest):
                        longest = match.group()
                        token = terminal
            if len(longest) == 0:
                raise Exception(
                    f"Unable to lex file at index {pos} (line {line_number}, column {column_number})"
                )
            else:
                sequence.append(Token(token, longest))
                pos += len(longest)
                for char in longest:
                    if char == '\n':
                        line_number += 1
                        column_number = 1
                    else:
                        column_number += 1

        return list(filter(lambda t: t.token not in self.ignored, sequence))
