"""Tests for the LALR(1) brute-force generator."""
from src.grammar import Grammar
from src.parser.shift_reduce import LALR_Brute_Force

from .conftest import (
    SIMPLE_GRAMMAR_TEXT,
    SIMPLE_TERMINALS_TEXT,
    NESTED_GRAMMAR_TEXT,
    NESTED_TERMINALS_TEXT,
    NULLABLE_GRAMMAR_TEXT,
    parse_with,
    collect_leaves,
)


class TestLALRBruteForceGenerator:
    def test_parse_simple(self):
        ast = parse_with(LALR_Brute_Force, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast is not None
        assert collect_leaves(ast) == ["a"]

    def test_parse_nested(self):
        ast = parse_with(LALR_Brute_Force, NESTED_GRAMMAR_TEXT, NESTED_TERMINALS_TEXT, "(foo,bar)")
        assert ast is not None
        assert collect_leaves(ast) == ["(", "foo", ",", "bar", ")"]

    def test_ast_structure(self):
        ast = parse_with(LALR_Brute_Force, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast.content == "start"
        assert len(ast.children) == 1
        assert ast.children[0].content == "expr"


class TestLALRBruteForceEpsilonInLookahead:
    """Bug: epsilon leaks into LALR_Brute_Force lookahead sets for nullable grammars."""

    def test_no_epsilon_in_action_table(self):
        """LALR_Brute_Force action table should never have '' as a terminal key."""
        grammar = Grammar(NULLABLE_GRAMMAR_TEXT)
        automaton = LALR_Brute_Force().generate(grammar)
        for (state, terminal), action in automaton._action.items():
            assert terminal != '', (
                f"Action table has epsilon ('') as terminal at state {state}"
            )
