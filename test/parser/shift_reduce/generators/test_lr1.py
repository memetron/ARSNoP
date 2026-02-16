"""Tests for the LR(1) generator."""
from arsnop.grammar import Grammar, Production
from arsnop.parser.shift_reduce import LR1, Item
from arsnop.parser.shift_reduce.generators.closure import lr1_closure

from .conftest import (
    SIMPLE_GRAMMAR_TEXT,
    SIMPLE_TERMINALS_TEXT,
    NESTED_GRAMMAR_TEXT,
    NESTED_TERMINALS_TEXT,
    NULLABLE_GRAMMAR_TEXT,
    parse_with,
    collect_leaves,
)


class TestLR1Generator:
    def test_parse_simple(self):
        ast = parse_with(LR1, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast is not None
        assert collect_leaves(ast) == ["a"]

    def test_parse_nested(self):
        ast = parse_with(LR1, NESTED_GRAMMAR_TEXT, NESTED_TERMINALS_TEXT, "(foo,bar)")
        assert ast is not None
        assert collect_leaves(ast) == ["(", "foo", ",", "bar", ")"]

    def test_ast_structure(self):
        ast = parse_with(LR1, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast.content == "start"
        assert len(ast.children) == 1
        assert ast.children[0].content == "expr"


class TestEpsilonInLookahead:
    """Bug: epsilon leaks into LR(1) lookahead sets for nullable grammars."""

    def test_lr1_closure_no_epsilon_in_lookahead(self):
        """LR1 closure should never produce items with '' in their lookahead."""
        grammar = Grammar(NULLABLE_GRAMMAR_TEXT)
        start_prod = Production("S'", [grammar.start_symbol])
        items = lr1_closure(
            grammar,
            [Item(start_prod, 0, frozenset({"$"}))]
        )
        for item in items:
            assert '' not in item.lookahead, (
                f"Epsilon found in lookahead of {item}"
            )

    def test_lr1_no_epsilon_in_action_table(self):
        """LR1 action table should never have '' as a terminal key."""
        grammar = Grammar(NULLABLE_GRAMMAR_TEXT)
        automaton = LR1().generate(grammar)
        for (state, terminal), action in automaton._action.items():
            assert terminal != '', (
                f"Action table has epsilon ('') as terminal at state {state}"
            )
