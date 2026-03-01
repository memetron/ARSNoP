"""Tests for shift-reduce state construction."""
from arsnop.grammar import Grammar
from arsnop.grammar.bnf_parser import parse_bnf
from arsnop.parser.shift_reduce import lr0_states, lr1_states


SIMPLE_GRAMMAR_BNF = ":GRAMMAR\nstart ::= expr ;\nexpr ::= TOK ;\n:TERMINALS\n"


class TestStateConstruction:
    def test_lr0_states_count(self):
        grammar = Grammar(parse_bnf(SIMPLE_GRAMMAR_BNF).rules)
        states, transitions = lr0_states(grammar)
        # S' -> .start, start -> .expr, expr -> .TOK  (state 0)
        # plus one state per symbol shift: start, expr, TOK
        assert len(states) == 4

    def test_lr0_transitions_exist(self):
        grammar = Grammar(parse_bnf(SIMPLE_GRAMMAR_BNF).rules)
        _, transitions = lr0_states(grammar)
        state0_symbols = {sym for (s, sym) in transitions if s == 0}
        assert "start" in state0_symbols
        assert "expr" in state0_symbols
        assert "TOK" in state0_symbols

    def test_lr1_states_count(self):
        grammar = Grammar(parse_bnf(SIMPLE_GRAMMAR_BNF).rules)
        states, transitions = lr1_states(grammar)
        assert len(states) == 4
