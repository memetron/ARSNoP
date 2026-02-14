"""Tests for shift-reduce parser generators (bug regressions)."""
from grammar.grammar import Grammar
from lexer.lexer import Lexer
from parser.shift_reduce.generators import LR0, LR1, SLR, LALR, LALR_Brute_Force


SIMPLE_GRAMMAR_TEXT = "start ::= expr\nexpr ::= TOK"
SIMPLE_TERMINALS_TEXT = "TOK a\nSPC [ ]\n.IGNORE\nSPC"


def _parse_with(generator_cls, grammar_text, terminals_text, input_text):
    grammar = Grammar(grammar_text)
    lexer = Lexer(terminals_text)
    automaton = generator_cls().generate(grammar)
    tokens = lexer.lex(input_text)
    return automaton.parse(tokens)


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
        ast = _parse_with(LR0, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast is not None

    def test_slr_parse_simple(self):
        ast = _parse_with(SLR, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast is not None


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
        ast = _parse_with(LALR, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast is not None
