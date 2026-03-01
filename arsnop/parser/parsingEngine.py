from ..lexer import Lexer
from ..ast import AST


class ParsingEngine:
    def parse(self, _text: str, _lexer: Lexer) -> AST:
        raise NotImplementedError
