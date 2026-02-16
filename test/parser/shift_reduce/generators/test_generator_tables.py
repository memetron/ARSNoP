"""Tests for Generator.generate_tables()."""

import pytest

from arsnop.grammar import Grammar
from arsnop.lexer import Lexer
from arsnop.parser.shift_reduce import (
    LR0, SLR, LR1, LALR, LALR_Brute_Force,
    GeneratorResult,
)

SIMPLE_GRAMMAR_TEXT = "start ::= expr\nexpr ::= TOK"
SIMPLE_TERMINALS_TEXT = "TOK a\nSPC [ ]\n.IGNORE\nSPC"


GENERATORS = [LR0, SLR, LR1, LALR, LALR_Brute_Force]


@pytest.fixture(params=GENERATORS, ids=lambda g: g.__name__)
def generator_cls(request):
    return request.param


class TestGenerateTablesReturnType:
    def test_returns_generator_result(self, generator_cls):
        grammar = Grammar(SIMPLE_GRAMMAR_TEXT)
        result = generator_cls().generate_tables(grammar)
        assert isinstance(result, GeneratorResult)

    def test_has_states(self, generator_cls):
        grammar = Grammar(SIMPLE_GRAMMAR_TEXT)
        result = generator_cls().generate_tables(grammar)
        assert isinstance(result.states, list)
        assert len(result.states) > 0

    def test_has_action_table(self, generator_cls):
        grammar = Grammar(SIMPLE_GRAMMAR_TEXT)
        result = generator_cls().generate_tables(grammar)
        assert isinstance(result.action_table, dict)
        assert len(result.action_table) > 0

    def test_has_goto_table(self, generator_cls):
        grammar = Grammar(SIMPLE_GRAMMAR_TEXT)
        result = generator_cls().generate_tables(grammar)
        assert isinstance(result.goto_table, dict)
        assert len(result.goto_table) > 0


class TestGenerateTablesConsistency:
    def test_tables_produce_same_parse_as_generate(self, generator_cls):
        grammar = Grammar(SIMPLE_GRAMMAR_TEXT)
        lexer = Lexer(SIMPLE_TERMINALS_TEXT)
        tokens = lexer.lex("a")

        # Parse via generate()
        automaton1 = generator_cls().generate(grammar)
        ast1 = automaton1.parse(tokens)

        # Parse via generate_tables()
        from arsnop.parser.shift_reduce.automaton import Automaton
        result = generator_cls().generate_tables(grammar)
        automaton2 = Automaton(result.goto_table, result.action_table)
        ast2 = automaton2.parse(tokens)

        assert str(ast1) == str(ast2)

    def test_result_is_frozen(self, generator_cls):
        grammar = Grammar(SIMPLE_GRAMMAR_TEXT)
        result = generator_cls().generate_tables(grammar)
        with pytest.raises(AttributeError):
            result.states = []  # type: ignore[misc]
