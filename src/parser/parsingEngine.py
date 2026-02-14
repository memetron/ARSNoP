from ..lexer import Token
from .ast import AST


class ParsingEngine:
    def parse(self, stream: list[Token]) -> AST:
        raise NotImplementedError