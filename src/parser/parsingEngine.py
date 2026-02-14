from src.lexer.token import Token
from src.parser.ast import AST


class ParsingEngine:
    def parse(self, stream: list[Token]) -> AST:
        raise NotImplementedError