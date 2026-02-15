"""Tests for shift-reduce state construction."""
import io
import contextlib

from src.grammar import Grammar, Production
from src.parser.shift_reduce import LALR, LR1, LALR_Brute_Force
from src.parser.shift_reduce import Item, lr0_states, lr1_states
from src.parser.shift_reduce.lr1 import _lr1_closure


SIMPLE_GRAMMAR_TEXT = "start ::= expr\nexpr ::= TOK"


# ===================================================================
# State construction correctness
# ===================================================================

class TestStateConstruction:
    def test_lr0_states_count(self):
        grammar = Grammar(SIMPLE_GRAMMAR_TEXT)
        states, transitions = lr0_states(grammar)
        # S' -> .start, start -> .expr, expr -> .TOK  (state 0)
        # plus one state per symbol shift: start, expr, TOK
        assert len(states) == 4

    def test_lr0_transitions_exist(self):
        grammar = Grammar(SIMPLE_GRAMMAR_TEXT)
        _, transitions = lr0_states(grammar)
        state0_symbols = {sym for (s, sym) in transitions if s == 0}
        assert "start" in state0_symbols
        assert "expr" in state0_symbols
        assert "TOK" in state0_symbols

    def test_lr1_states_count(self):
        grammar = Grammar(SIMPLE_GRAMMAR_TEXT)
        states, transitions = lr1_states(grammar)
        assert len(states) == 4


# ===================================================================
# Bug regressions
# ===================================================================

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
        nullable_grammar = Grammar(self.NULLABLE_GRAMMAR)
        automaton = LR1().generate(nullable_grammar)
        for (state, terminal), action in automaton._action.items():
            assert terminal != '', (
                f"Action table has epsilon ('') as terminal at state {state}"
            )

    def test_lalr_no_epsilon_in_action_table(self):
        nullable_grammar = Grammar(self.NULLABLE_GRAMMAR)
        automaton = LALR().generate(nullable_grammar)
        for (state, terminal), action in automaton._action.items():
            assert terminal != '', (
                f"Action table has epsilon ('') as terminal at state {state}"
            )

    def test_lalr_brute_force_no_epsilon_in_action_table(self):
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
