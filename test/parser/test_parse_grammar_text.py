"""Tests for parse_bnf() (replaces the old parse_grammar_text tests)."""

import pytest

from arsnop.grammar import parse_bnf


VALID_TEXT = ":GRAMMAR\nstart ::= A ;\n:TERMINALS\nA /a/ ;\n"


class TestParseBnf:
    def test_returns_bnfspec(self):
        spec = parse_bnf(VALID_TEXT)
        assert len(spec.rules) == 1
        assert len(spec.terminals) == 1

    def test_rule_parsed(self):
        spec = parse_bnf(VALID_TEXT)
        rule = spec.rules[0]
        assert rule.lhs == "start"
        assert len(rule.alternatives) == 1
        assert rule.alternatives[0].symbols == ("A",)

    def test_terminal_parsed(self):
        spec = parse_bnf(VALID_TEXT)
        terminal = spec.terminals[0]
        assert terminal.name == "A"
        assert terminal.pattern == "a"

    def test_raises_on_missing_grammar(self):
        with pytest.raises((ValueError, Exception)):
            parse_bnf(":TERMINALS\nA /a/ ;\n")

    def test_raises_on_missing_terminals(self):
        with pytest.raises((ValueError, Exception)):
            parse_bnf(":GRAMMAR\nstart ::= A ;\n")

    def test_raises_on_empty_string(self):
        with pytest.raises((ValueError, Exception)):
            parse_bnf("")

    def test_multiline_grammar(self):
        text = ":GRAMMAR\nstart ::= a b ;\na ::= A ;\nb ::= B ;\n:TERMINALS\nA /a/ ;\nB /b/ ;\n"
        spec = parse_bnf(text)
        lhs_names = [r.lhs for r in spec.rules]
        assert "start" in lhs_names
        assert "a" in lhs_names
        assert "b" in lhs_names
        terminal_names = [t.name for t in spec.terminals]
        assert "A" in terminal_names
        assert "B" in terminal_names
