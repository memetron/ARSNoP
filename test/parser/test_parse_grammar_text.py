"""Tests for parse_grammar_text()."""

import pytest

from arsnop.parser import parse_grammar_text


VALID_TEXT = ":GRAMMAR\nstart ::= A\n:TERMINALS\nA a\n"


class TestParseGrammarText:
    def test_returns_tuple(self):
        result = parse_grammar_text(VALID_TEXT)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_grammar_section(self):
        grammar, _ = parse_grammar_text(VALID_TEXT)
        assert "start ::= A" in grammar

    def test_terminals_section(self):
        _, terminals = parse_grammar_text(VALID_TEXT)
        assert "A a" in terminals

    def test_raises_on_missing_grammar(self):
        with pytest.raises(ValueError, match="must contain"):
            parse_grammar_text(":TERMINALS\nA a\n")

    def test_raises_on_missing_terminals(self):
        with pytest.raises(ValueError, match="must contain"):
            parse_grammar_text(":GRAMMAR\nstart ::= A\n")

    def test_raises_on_empty_string(self):
        with pytest.raises(ValueError, match="must contain"):
            parse_grammar_text("")

    def test_raises_on_garbage(self):
        with pytest.raises(ValueError, match="must contain"):
            parse_grammar_text("this is not a grammar file")

    def test_multiline_grammar(self):
        text = ":GRAMMAR\nstart ::= a b\na ::= A\nb ::= B\n:TERMINALS\nA a\nB b\n"
        grammar, terminals = parse_grammar_text(text)
        assert "a ::= A" in grammar
        assert "b ::= B" in grammar
        assert "A a" in terminals
