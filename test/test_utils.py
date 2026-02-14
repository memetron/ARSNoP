"""Tests for src/utils.py — flatten and print_states."""
import io
import contextlib

from src.utils import flatten, print_states
from src.grammar import Production
from src.parser.shift_reduce import Item, State


class TestFlatten:
    def test_flat_list(self):
        assert flatten([1, 2, 3]) == [1, 2, 3]

    def test_nested_list(self):
        assert flatten([1, [2, 3]]) == [1, 2, 3]

    def test_deeply_nested(self):
        assert flatten([1, [2, [3, [4]]]]) == [1, 2, 3, 4]

    def test_single_element(self):
        assert flatten(5) == [5]

    def test_empty_list(self):
        assert flatten([]) == []

    def test_all_nested_empty(self):
        assert flatten([[], [[]]]) == []

    def test_strings_not_flattened(self):
        assert flatten(["hello", "world"]) == ["hello", "world"]

    def test_mixed_types(self):
        assert flatten([1, ["a", [True]]]) == [1, "a", True]


class TestPrintStates:
    def test_single_state(self):
        prod = Production("start", ["expr"])
        item = Item(prod, 0, frozenset({"$"}))
        state = State([item])
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            print_states([state])
        output = f.getvalue()
        assert "STATE_0:" in output
        assert "start" in output

    def test_multiple_states(self):
        prod1 = Production("start", ["expr"])
        prod2 = Production("expr", ["TOK"])
        state0 = State([Item(prod1, 0, frozenset({"$"}))])
        state1 = State([Item(prod2, 0, frozenset({"$"}))])
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            print_states([state0, state1])
        output = f.getvalue()
        assert "STATE_0:" in output
        assert "STATE_1:" in output
