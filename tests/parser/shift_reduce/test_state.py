"""Tests for shift-reduce state construction (bug regressions)."""
import io
import contextlib

from grammar.grammar import Grammar
from grammar.production import Production
from parser.shift_reduce.state import lr0_states, _lr1_closure
from parser.shift_reduce.state import Item


SIMPLE_GRAMMAR_TEXT = "start ::= expr\nexpr ::= TOK"


class TestEpsilonInLookahead:
    """Bug: _lr1_closure leaks epsilon ('') into lookahead sets."""

    # Use | syntax for nullable rules so trailing spaces survive text.strip()
    NULLABLE_GRAMMAR = "start ::= A B c\nA ::= a | \nB ::= b | "

    def test_lr1_closure_no_epsilon_in_lookahead(self):
        nullable_grammar = Grammar(self.NULLABLE_GRAMMAR)
        start_prod = Production("S'", [nullable_grammar.start_symbol])
        items = _lr1_closure(
            nullable_grammar,
            [Item(start_prod, 0, frozenset({"$"}))]
        )
        for item in items:
            assert '' not in item.lookahead, (
                f"Epsilon found in lookahead of {item}"
            )

    def test_lr1_no_epsilon_in_action_table(self):
        from parser.shift_reduce.generators import LR1
        nullable_grammar = Grammar(self.NULLABLE_GRAMMAR)
        automaton = LR1().generate(nullable_grammar)
        for (state, terminal), action in automaton._action.items():
            assert terminal != '', (
                f"Action table has epsilon ('') as terminal at state {state}"
            )

    def test_lalr_no_epsilon_in_action_table(self):
        from parser.shift_reduce.generators import LALR
        nullable_grammar = Grammar(self.NULLABLE_GRAMMAR)
        automaton = LALR().generate(nullable_grammar)
        for (state, terminal), action in automaton._action.items():
            assert terminal != '', (
                f"Action table has epsilon ('') as terminal at state {state}"
            )

    def test_lalr_brute_force_no_epsilon_in_action_table(self):
        from parser.shift_reduce.generators import LALR_Brute_Force
        nullable_grammar = Grammar(self.NULLABLE_GRAMMAR)
        automaton = LALR_Brute_Force().generate(nullable_grammar)
        for (state, terminal), action in automaton._action.items():
            assert terminal != '', (
                f"Action table has epsilon ('') as terminal at state {state}"
            )


class TestDebugPrintStates:
    """Bug: lr0_states unconditionally prints to stdout."""

    def test_lr0_states_no_stdout(self):
        grammar = Grammar(SIMPLE_GRAMMAR_TEXT)
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            lr0_states(grammar)
        output = f.getvalue()
        assert output == "", (
            f"lr0_states printed to stdout: {output[:200]}"
        )
