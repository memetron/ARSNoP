from typing import Iterator

from lexer.token import Token


class ParsingEngine:
    def parse(self, stream: Iterator[Token]):
        raise NotImplementedError