"""Tests for src/lexer/lexer.py."""
import pytest

from arsnop.grammar.bnf_types import TerminalSpec
from arsnop.lexer import Lexer


SIMPLE_TERMINAL_SPECS = [
    TerminalSpec("NUM", "[0-9]+"),
    TerminalSpec("ID", "[a-z]+"),
    TerminalSpec("SPC", "[ ]"),
]
SIMPLE_IGNORED = ["SPC"]

MULTI_TERMINAL_SPECS = [
    TerminalSpec("NUM", "[0-9]+"),
    TerminalSpec("OP", "[+\\-*/]"),
    TerminalSpec("SPC", "[ ]"),
]
MULTI_IGNORED = ["SPC"]


class TestLexerInit:
    def test_terminals_parsed(self):
        lexer = Lexer(SIMPLE_TERMINAL_SPECS, SIMPLE_IGNORED)
        assert "NUM" in lexer.terminals
        assert "ID" in lexer.terminals

    def test_ignored_parsed(self):
        lexer = Lexer(SIMPLE_TERMINAL_SPECS, SIMPLE_IGNORED)
        assert "SPC" in lexer.ignored


class TestLex:
    def test_single_token(self):
        lexer = Lexer(SIMPLE_TERMINAL_SPECS, SIMPLE_IGNORED)
        tokens = lexer.lex("42")
        assert len(tokens) == 1
        assert tokens[0].token == "NUM"
        assert tokens[0].lexeme == "42"

    def test_multiple_tokens(self):
        lexer = Lexer(MULTI_TERMINAL_SPECS, MULTI_IGNORED)
        tokens = lexer.lex("1 + 2")
        assert len(tokens) == 3
        assert tokens[0].token == "NUM"
        assert tokens[0].lexeme == "1"
        assert tokens[1].token == "OP"
        assert tokens[1].lexeme == "+"
        assert tokens[2].token == "NUM"
        assert tokens[2].lexeme == "2"

    def test_ignored_terminals_filtered(self):
        lexer = Lexer(SIMPLE_TERMINAL_SPECS, SIMPLE_IGNORED)
        tokens = lexer.lex("foo 42 bar")
        token_types = [t.token for t in tokens]
        assert "SPC" not in token_types
        assert len(tokens) == 3

    def test_longest_match(self):
        lexer = Lexer(SIMPLE_TERMINAL_SPECS, SIMPLE_IGNORED)
        tokens = lexer.lex("123")
        assert len(tokens) == 1
        assert tokens[0].lexeme == "123"

    def test_lex_error(self):
        lexer = Lexer(SIMPLE_TERMINAL_SPECS, SIMPLE_IGNORED)
        with pytest.raises(Exception, match="Unable to lex"):
            lexer.lex("!!!")

    def test_empty_input(self):
        lexer = Lexer(SIMPLE_TERMINAL_SPECS, SIMPLE_IGNORED)
        tokens = lexer.lex("")
        assert tokens == []

    def test_adjacent_tokens(self):
        lexer = Lexer(SIMPLE_TERMINAL_SPECS, SIMPLE_IGNORED)
        tokens = lexer.lex("abc123")
        assert len(tokens) == 2
        assert tokens[0].token == "ID"
        assert tokens[0].lexeme == "abc"
        assert tokens[1].token == "NUM"
        assert tokens[1].lexeme == "123"


class TestLexerMultiTerminals:
    def test_arithmetic_expression(self):
        lexer = Lexer(MULTI_TERMINAL_SPECS, MULTI_IGNORED)
        tokens = lexer.lex("10 - 3 * 2")
        assert len(tokens) == 5
        assert tokens[0].lexeme == "10"
        assert tokens[1].lexeme == "-"
        assert tokens[2].lexeme == "3"
        assert tokens[3].lexeme == "*"
        assert tokens[4].lexeme == "2"

    def test_literal_regex_terminal(self):
        """Terminals defined with literal strings as regex work correctly."""
        lexer = Lexer(
            [TerminalSpec("KEYWORD", "and"), TerminalSpec("ID", "[a-z]+"), TerminalSpec("SPC", "[ ]")],
            ["SPC"],
        )
        tokens = lexer.lex("foo and bar")
        assert len(tokens) == 3
        assert tokens[1].token == "KEYWORD"
        assert tokens[1].lexeme == "and"

    def test_inline_terminal_sets_token_inline(self):
        """Tokens produced from an inline TerminalSpec have token.inline=True."""
        lexer = Lexer(
            [TerminalSpec("ID", "[a-z]+"), TerminalSpec("SEP", ",", inline=True)],
            [],
        )
        tokens = lexer.lex("a,b")
        assert tokens[0].inline is False   # ID
        assert tokens[1].inline is True    # SEP is inline
        assert tokens[2].inline is False   # ID
