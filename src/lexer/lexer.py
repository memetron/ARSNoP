import re

from .token import Token

_LEXER_FILE_RE = re.compile(r"(.*)\.IGNORE(.*)", re.DOTALL)
_TERMINAL_RE = re.compile(r"([A-Z_]+) (.+)")


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

    def __init__(self, terminals: str) -> None:
        """
        Initializes the Lexer with terminal definitions.

        Terminal definitions are specified in a string with sections for exact matches, standard matches,
        and ignored terminals.

        Args:
            terminals (str): A string containing terminal definitions in the format:
                "<STANDARD_TERMINALS>.EXACT<EXACT_TERMINALS>.IGNORE<IGNORED_TERMINALS>"
        """
        self.terminals: dict[str, re.Pattern[str]] = {}
        match = re.match(_LEXER_FILE_RE, terminals)
        if not match:
            raise ValueError("Terminal definitions must contain a .IGNORE section")
        terminals, ignored = match.groups()
        self.ignored: list[str] = ignored.split('\n')

        lines = terminals.split('\n')
        for line in lines:
            match = re.match(_TERMINAL_RE, line)
            if match:
                terminal, regex = match.groups()
                self.terminals[terminal] = re.compile(f"^{regex}")

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
