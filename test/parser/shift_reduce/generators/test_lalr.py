"""Tests for the LALR(1) generator."""
from arsnop.grammar import Grammar
from arsnop.parser.shift_reduce import LALR

from .conftest import (
    SIMPLE_GRAMMAR_TEXT,
    SIMPLE_TERMINALS_TEXT,
    NESTED_GRAMMAR_TEXT,
    NESTED_TERMINALS_TEXT,
    NULLABLE_GRAMMAR_TEXT,
    parse_with,
    collect_leaves,
)


class TestLALRGenerator:
    def test_parse_simple(self):
        ast = parse_with(LALR, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast is not None
        assert collect_leaves(ast) == ["a"]

    def test_parse_nested(self):
        ast = parse_with(LALR, NESTED_GRAMMAR_TEXT, NESTED_TERMINALS_TEXT, "(foo,bar)")
        assert ast is not None
        assert collect_leaves(ast) == ["(", "foo", ",", "bar", ")"]

    def test_ast_structure(self):
        ast = parse_with(LALR, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast.content == "start"
        assert len(ast.children) == 1
        assert ast.children[0].content == "expr"


class TestLALRMissingNoneGuard:
    """Bug: LALR generator omits None check on shift, unlike all other generators."""

    def test_no_none_shift_entries(self):
        grammar = Grammar(SIMPLE_GRAMMAR_TEXT)
        automaton = LALR().generate(grammar)
        for key, value in automaton._action.items():
            if value[0] == "shift":
                assert value[1] is not None, (
                    f"Action table has ('shift', None) at {key}"
                )

    def test_lalr_parse_simple(self):
        ast = parse_with(LALR, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast is not None


class TestLALREpsilonInLookahead:
    """Bug: epsilon leaks into LALR lookahead sets for nullable grammars."""

    def test_no_epsilon_in_action_table(self):
        """LALR action table should never have '' as a terminal key."""
        grammar = Grammar(NULLABLE_GRAMMAR_TEXT)
        automaton = LALR().generate(grammar)
        for (state, terminal), action in automaton._action.items():
            assert terminal != '', (
                f"Action table has epsilon ('') as terminal at state {state}"
            )
