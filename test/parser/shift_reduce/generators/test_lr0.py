"""Tests for LR(0) and SLR(1) generators."""
import io
import contextlib

from arsnop.grammar import Grammar
from arsnop.parser.shift_reduce import LR0, SLR, lr0_states

from .conftest import (
    SIMPLE_GRAMMAR_TEXT,
    SIMPLE_TERMINALS_TEXT,
    NESTED_GRAMMAR_TEXT,
    NESTED_TERMINALS_TEXT,
    parse_with,
    collect_leaves,
)


class TestSLRGenerator:
    def test_parse_simple(self):
        ast = parse_with(SLR, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast is not None
        assert collect_leaves(ast) == ["a"]

    def test_parse_nested(self):
        ast = parse_with(SLR, NESTED_GRAMMAR_TEXT, NESTED_TERMINALS_TEXT, "(foo,bar)")
        assert ast is not None
        assert collect_leaves(ast) == ["(", "foo", ",", "bar", ")"]

    def test_ast_structure(self):
        ast = parse_with(SLR, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast.content == "start"
        assert len(ast.children) == 1
        assert ast.children[0].content == "expr"


class TestLR0MissingDollarReduce:
    """Bug: LR0 omits reduce actions for '$', causing KeyError at end-of-input."""

    def test_lr0_action_table_has_dollar_reduce(self):
        grammar = Grammar(SIMPLE_GRAMMAR_TEXT)
        automaton = LR0().generate(grammar)
        dollar_reduces = [
            (k, v) for k, v in automaton._action.items()
            if k[1] == '$' and v[0] == "reduce"
        ]
        assert len(dollar_reduces) > 0, (
            "LR0 action table has no reduce entries for '$'"
        )

    def test_lr0_parse_simple(self):
        ast = parse_with(LR0, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast is not None

    def test_slr_parse_simple(self):
        ast = parse_with(SLR, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast is not None


class TestDebugPrintStates:
    """Bug: lr0_states had a debug print_states call left in."""

    def test_lr0_states_no_stdout(self):
        """lr0_states should not print to stdout."""
        grammar = Grammar(SIMPLE_GRAMMAR_TEXT)
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            lr0_states(grammar)
        output = f.getvalue()
        assert output == "", (
            f"lr0_states printed to stdout: {output[:200]}"
        )
