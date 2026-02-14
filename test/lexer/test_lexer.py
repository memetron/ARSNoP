"""Tests for src/lexer/lexer.py."""
import pytest

from src.lexer import Lexer


# Minimal terminal definition: standard terminals + .IGNORE section
SIMPLE_TERMINALS = "NUM [0-9]+\nID [a-z]+\nSPC [ ]\n.IGNORE\nSPC"

MULTI_TERMINALS = "NUM [0-9]+\nOP [+\\-*/]\nSPC [ ]\n.IGNORE\nSPC"


class TestLexerInit:
    def test_terminals_parsed(self):
        lexer = Lexer(SIMPLE_TERMINALS)
        assert "NUM" in lexer.terminals
        assert "ID" in lexer.terminals

    def test_ignored_parsed(self):
        lexer = Lexer(SIMPLE_TERMINALS)
        assert "SPC" in lexer.ignored


class TestLex:
    def test_single_token(self):
        lexer = Lexer(SIMPLE_TERMINALS)
        tokens = lexer.lex("42")
        assert len(tokens) == 1
        assert tokens[0].token == "NUM"
        assert tokens[0].lexeme == "42"

    def test_multiple_tokens(self):
        lexer = Lexer(MULTI_TERMINALS)
        tokens = lexer.lex("1 + 2")
        assert len(tokens) == 3
        assert tokens[0].token == "NUM"
        assert tokens[0].lexeme == "1"
        assert tokens[1].token == "OP"
        assert tokens[1].lexeme == "+"
        assert tokens[2].token == "NUM"
        assert tokens[2].lexeme == "2"

    def test_ignored_terminals_filtered(self):
        lexer = Lexer(SIMPLE_TERMINALS)
        tokens = lexer.lex("foo 42 bar")
        token_types = [t.token for t in tokens]
        assert "SPC" not in token_types
        assert len(tokens) == 3

    def test_longest_match(self):
        lexer = Lexer(SIMPLE_TERMINALS)
        tokens = lexer.lex("123")
        assert len(tokens) == 1
        assert tokens[0].lexeme == "123"

    def test_lex_error(self):
        lexer = Lexer(SIMPLE_TERMINALS)
        with pytest.raises(Exception, match="Unable to lex"):
            lexer.lex("!!!")

    def test_empty_input(self):
        lexer = Lexer(SIMPLE_TERMINALS)
        tokens = lexer.lex("")
        assert tokens == []

    def test_adjacent_tokens(self):
        lexer = Lexer(SIMPLE_TERMINALS)
        tokens = lexer.lex("abc123")
        assert len(tokens) == 2
        assert tokens[0].token == "ID"
        assert tokens[0].lexeme == "abc"
        assert tokens[1].token == "NUM"
        assert tokens[1].lexeme == "123"


class TestLexerMultiTerminals:
    def test_arithmetic_expression(self):
        lexer = Lexer(MULTI_TERMINALS)
        tokens = lexer.lex("10 - 3 * 2")
        assert len(tokens) == 5
        assert tokens[0].lexeme == "10"
        assert tokens[1].lexeme == "-"
        assert tokens[2].lexeme == "3"
        assert tokens[3].lexeme == "*"
        assert tokens[4].lexeme == "2"

    def test_literal_regex_terminal(self):
        """Terminals defined with literal strings as regex work correctly."""
        terminals = "KEYWORD and\nID [a-z]+\nSPC [ ]\n.IGNORE\nSPC"
        lexer = Lexer(terminals)
        tokens = lexer.lex("foo and bar")
        assert len(tokens) == 3
        assert tokens[1].token == "KEYWORD"
        assert tokens[1].lexeme == "and"
