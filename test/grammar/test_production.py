"""Tests for src/grammar/production.py."""
from src.grammar import Production


class TestProduction:
    def test_init(self):
        p = Production("A", ["B", "C"])
        assert p.lhs == "A"
        assert p.rhs == ["B", "C"]

    def test_str(self):
        p = Production("expr", ["NUM", "OP", "NUM"])
        assert str(p) == "expr ::= NUM OP NUM"

    def test_empty_rhs(self):
        p = Production("A", [])
        assert p.lhs == "A"
        assert p.rhs == []
        assert str(p) == "A ::= "

    def test_single_symbol_rhs(self):
        p = Production("start", ["expr"])
        assert str(p) == "start ::= expr"
