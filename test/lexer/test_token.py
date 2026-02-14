"""Tests for src/lexer/token.py."""
from src.lexer.token import Token


class TestToken:
    def test_init(self):
        t = Token("NUM", "42")
        assert t.token == "NUM"
        assert t.lexeme == "42"

    def test_str(self):
        t = Token("ID", "foo")
        assert str(t) == 'token(ID, "foo")'

    def test_different_tokens(self):
        t1 = Token("NUM", "1")
        t2 = Token("OP", "+")
        assert t1.token != t2.token
        assert t1.lexeme != t2.lexeme
