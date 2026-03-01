"""Tests for src/lexer/lexer.py."""
import pytest

from arsnop.grammar.bnf_types import TerminalSpec
from arsnop.lexer import Lexer, Token


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


def _lex_all(lexer: Lexer, text: str) -> list[Token]:
    """Lex a full string with all terminals valid at every position."""
    all_terminals = frozenset(lexer.terminals.keys())
    tokens: list[Token] = []
    pos = 0
    while True:
        tok, pos = lexer.lex_one(text, pos, all_terminals)
        if tok is None:
            break
        tokens.append(tok)
    return tokens


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
        tokens = _lex_all(lexer,"42")
        assert len(tokens) == 1
        assert tokens[0].token == "NUM"
        assert tokens[0].lexeme == "42"

    def test_multiple_tokens(self):
        lexer = Lexer(MULTI_TERMINAL_SPECS, MULTI_IGNORED)
        tokens = _lex_all(lexer,"1 + 2")
        assert len(tokens) == 3
        assert tokens[0].token == "NUM"
        assert tokens[0].lexeme == "1"
        assert tokens[1].token == "OP"
        assert tokens[1].lexeme == "+"
        assert tokens[2].token == "NUM"
        assert tokens[2].lexeme == "2"

    def test_ignored_terminals_filtered(self):
        lexer = Lexer(SIMPLE_TERMINAL_SPECS, SIMPLE_IGNORED)
        tokens = _lex_all(lexer,"foo 42 bar")
        token_types = [t.token for t in tokens]
        assert "SPC" not in token_types
        assert len(tokens) == 3

    def test_longest_match(self):
        lexer = Lexer(SIMPLE_TERMINAL_SPECS, SIMPLE_IGNORED)
        tokens = _lex_all(lexer,"123")
        assert len(tokens) == 1
        assert tokens[0].lexeme == "123"

    def test_lex_error(self):
        lexer = Lexer(SIMPLE_TERMINAL_SPECS, SIMPLE_IGNORED)
        with pytest.raises(Exception, match="Unexpected character"):
            _lex_all(lexer,"!!!")

    def test_empty_input(self):
        lexer = Lexer(SIMPLE_TERMINAL_SPECS, SIMPLE_IGNORED)
        tokens = _lex_all(lexer,"")
        assert tokens == []

    def test_adjacent_tokens(self):
        lexer = Lexer(SIMPLE_TERMINAL_SPECS, SIMPLE_IGNORED)
        tokens = _lex_all(lexer,"abc123")
        assert len(tokens) == 2
        assert tokens[0].token == "ID"
        assert tokens[0].lexeme == "abc"
        assert tokens[1].token == "NUM"
        assert tokens[1].lexeme == "123"


class TestLexOne:
    def test_matches_single_token(self):
        lexer = Lexer(SIMPLE_TERMINAL_SPECS, SIMPLE_IGNORED)
        token, new_pos = lexer.lex_one("abc", 0, frozenset({"ID"}))
        assert token is not None
        assert token.token == "ID"
        assert token.lexeme == "abc"
        assert new_pos == 3

    def test_returns_none_at_end_of_input(self):
        lexer = Lexer(SIMPLE_TERMINAL_SPECS, SIMPLE_IGNORED)
        token, new_pos = lexer.lex_one("", 0, frozenset({"ID"}))
        assert token is None
        assert new_pos == 0

    def test_skips_ignored_before_matching(self):
        lexer = Lexer(SIMPLE_TERMINAL_SPECS, SIMPLE_IGNORED)
        token, new_pos = lexer.lex_one("  42", 0, frozenset({"NUM"}))
        assert token is not None
        assert token.token == "NUM"
        assert token.lexeme == "42"
        assert new_pos == 4

    def test_returns_none_after_trailing_ignored(self):
        lexer = Lexer(SIMPLE_TERMINAL_SPECS, SIMPLE_IGNORED)
        token, _ = lexer.lex_one("   ", 0, frozenset({"NUM"}))
        assert token is None

    def test_only_matches_valid_terminals(self):
        """Keyword excluded from valid set falls through to ID."""
        lexer = Lexer(
            [TerminalSpec("TYPE", "type"), TerminalSpec("ID", "[a-zA-Z]\\w*"), TerminalSpec("SPC", "[ ]")],
            ["SPC"],
        )
        token, _ = lexer.lex_one("type", 0, frozenset({"ID"}))
        assert token is not None
        assert token.token == "ID"
        assert token.lexeme == "type"

    def test_keyword_matched_when_only_keyword_valid(self):
        """When only the keyword terminal is valid, 'type' is lexed as TYPE."""
        lexer = Lexer(
            [TerminalSpec("TYPE", "type"), TerminalSpec("ID", "[a-zA-Z]\\w*"), TerminalSpec("SPC", "[ ]")],
            ["SPC"],
        )
        token, _ = lexer.lex_one("type", 0, frozenset({"TYPE"}))
        assert token is not None
        assert token.token == "TYPE"

    def test_raises_on_unmatchable_input(self):
        lexer = Lexer(SIMPLE_TERMINAL_SPECS, SIMPLE_IGNORED)
        with pytest.raises(Exception, match="Unexpected character"):
            lexer.lex_one("!!!", 0, frozenset({"NUM", "ID"}))

    def test_longest_match_among_valid(self):
        lexer = Lexer(
            [TerminalSpec("AB", "ab"), TerminalSpec("ABC", "abc"), TerminalSpec("SPC", "[ ]")],
            ["SPC"],
        )
        token, _ = lexer.lex_one("abc", 0, frozenset({"AB", "ABC"}))
        assert token is not None
        assert token.token == "ABC"
        assert token.lexeme == "abc"


class TestLexerMultiTerminals:
    def test_arithmetic_expression(self):
        lexer = Lexer(MULTI_TERMINAL_SPECS, MULTI_IGNORED)
        tokens = _lex_all(lexer,"10 - 3 * 2")
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
        tokens = _lex_all(lexer,"foo and bar")
        assert len(tokens) == 3
        assert tokens[1].token == "KEYWORD"
        assert tokens[1].lexeme == "and"

    def test_inline_terminal_sets_token_inline(self):
        """Tokens produced from an inline TerminalSpec have token.inline=True."""
        lexer = Lexer(
            [TerminalSpec("ID", "[a-z]+"), TerminalSpec("SEP", ",", inline=True)],
            [],
        )
        tokens = _lex_all(lexer,"a,b")
        assert tokens[0].inline is False   # ID
        assert tokens[1].inline is True    # SEP is inline
        assert tokens[2].inline is False   # ID
