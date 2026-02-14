"""Tests targeting known bugs in the parser generators."""
import io
import contextlib

from src.grammar.grammar import Grammar
from src.grammar.production import Production
from src.lexer.lexer import Lexer
from src.parser.shift_reduce.generators import LR0, LR1, SLR, LALR, LALR_Brute_Force
from src.parser.shift_reduce.state import lr0_states, _lr1_closure
from src.parser.shift_reduce.state import Item


# A minimal grammar: start ::= expr, expr ::= TOK
SIMPLE_GRAMMAR_TEXT = "start ::= expr\nexpr ::= TOK"
SIMPLE_TERMINALS_TEXT = "TOK a\nSPC [ ]\n.IGNORE\nSPC"


def _make_grammar():
    return Grammar(SIMPLE_GRAMMAR_TEXT)


def _make_lexer():
    return Lexer(SIMPLE_TERMINALS_TEXT)


def _parse_with(generator_cls, text="a"):
    grammar = _make_grammar()
    lexer = _make_lexer()
    automaton = generator_cls().generate(grammar)
    tokens = lexer.lex(text)
    return automaton.parse(tokens)


# ---------- Bug 1: LALR missing None guard on shift action ----------

class TestLALRMissingNoneGuard:
    def test_no_none_shift_entries(self):
        """LALR action table should not contain ("shift", None) entries."""
        grammar = _make_grammar()
        automaton = LALR().generate(grammar)
        for key, value in automaton._action.items():
            if value[0] == "shift":
                assert value[1] is not None, (
                    f"Action table has ('shift', None) at {key}"
                )

    def test_lalr_parse_simple(self):
        """LALR should successfully parse a simple input."""
        ast = _parse_with(LALR)
        assert ast is not None


# ---------- Bug 2: LR0 missing reduce on '$' ----------

class TestLR0MissingDollarReduce:
    def test_lr0_action_table_has_dollar_reduce(self):
        """LR0 action table should have reduce entries for '$' in reduce states."""
        grammar = _make_grammar()
        automaton = LR0().generate(grammar)
        # There should be at least one reduce action on '$' besides accept
        dollar_reduces = [
            (k, v) for k, v in automaton._action.items()
            if k[1] == '$' and v[0] == "reduce"
        ]
        assert len(dollar_reduces) > 0, (
            "LR0 action table has no reduce entries for '$'"
        )

    def test_lr0_parse_simple(self):
        """LR0 should successfully parse a simple input without KeyError."""
        ast = _parse_with(LR0)
        assert ast is not None

    def test_slr_parse_simple(self):
        """SLR (which also uses lr0_states) should parse successfully."""
        ast = _parse_with(SLR)
        assert ast is not None


# ---------- Bug 3: Epsilon leaks into LR1 lookahead sets ----------

class TestEpsilonInLookahead:
    # Use | syntax for nullable rules so trailing spaces survive text.strip()
    NULLABLE_GRAMMAR = "start ::= A B c\nA ::= a | \nB ::= b | "

    def test_lr1_closure_no_epsilon_in_lookahead(self):
        """LR1 closure should never produce items with '' in their lookahead."""
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
        """LR1 action table should never have '' as a terminal key."""
        nullable_grammar = Grammar(self.NULLABLE_GRAMMAR)
        automaton = LR1().generate(nullable_grammar)
        for (state, terminal), action in automaton._action.items():
            assert terminal != '', (
                f"Action table has epsilon ('') as terminal at state {state}"
            )

    def test_lalr_no_epsilon_in_action_table(self):
        """LALR action table should never have '' as a terminal key."""
        nullable_grammar = Grammar(self.NULLABLE_GRAMMAR)
        automaton = LALR().generate(nullable_grammar)
        for (state, terminal), action in automaton._action.items():
            assert terminal != '', (
                f"Action table has epsilon ('') as terminal at state {state}"
            )

    def test_lalr_brute_force_no_epsilon_in_action_table(self):
        """LALR_Brute_Force action table should never have '' as a terminal key."""
        nullable_grammar = Grammar(self.NULLABLE_GRAMMAR)
        automaton = LALR_Brute_Force().generate(nullable_grammar)
        for (state, terminal), action in automaton._action.items():
            assert terminal != '', (
                f"Action table has epsilon ('') as terminal at state {state}"
            )


# ---------- Bug 4: Debug print_states left in lr0_states ----------

class TestDebugPrintStates:
    def test_lr0_states_no_stdout(self):
        """lr0_states should not print to stdout."""
        grammar = _make_grammar()
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            lr0_states(grammar)
        output = f.getvalue()
        assert output == "", (
            f"lr0_states printed to stdout: {output[:200]}"
        )
