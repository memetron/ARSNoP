"""Tests for the Earley parser."""
import pytest

from src.grammar import Grammar
from src.lexer import Lexer, Token
from src.parser.earley import Earley


SIMPLE_GRAMMAR_TEXT = "start ::= expr\nexpr ::= TOK"
SIMPLE_TERMINALS_TEXT = "TOK a\nSPC [ ]\n.IGNORE\nSPC"

ARITH_GRAMMAR_TEXT = "start ::= expr\nexpr ::= expr OP NUM | NUM"
ARITH_TERMINALS_TEXT = "OP [+\\-]\nNUM [0-9]+\nSPC [ ]\n.IGNORE\nSPC"

NESTED_GRAMMAR_TEXT = (
    "start ::= list\n"
    "list ::= LP items RP\n"
    "items ::= ITEM SEP items | ITEM"
)
NESTED_TERMINALS_TEXT = "LP \\(\nRP \\)\nSEP ,\nITEM [a-z]+\nSPC [ ]\n.IGNORE\nSPC"


def _parse(grammar_text, terminals_text, input_text):
    grammar = Grammar(grammar_text)
    lexer = Lexer(terminals_text)
    engine = Earley(grammar)
    tokens = lexer.lex(input_text)
    return engine.parse(tokens)


def _collect_leaves(ast):
    if not ast.children:
        if isinstance(ast.content, Token):
            return [ast.content.lexeme]
        return [str(ast.content)]
    leaves = []
    for child in ast.children:
        leaves.extend(_collect_leaves(child))
    return leaves


class TestEarleyParser:
    def test_parse_simple(self):
        ast = _parse(SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast is not None
        assert _collect_leaves(ast) == ["a"]

    def test_parse_arithmetic(self):
        ast = _parse(ARITH_GRAMMAR_TEXT, ARITH_TERMINALS_TEXT, "1 + 2")
        assert ast is not None
        assert _collect_leaves(ast) == ["1", "+", "2"]

    def test_parse_nested(self):
        ast = _parse(NESTED_GRAMMAR_TEXT, NESTED_TERMINALS_TEXT, "(foo,bar,baz)")
        assert ast is not None
        assert _collect_leaves(ast) == ["(", "foo", ",", "bar", ",", "baz", ")"]

    def test_reject_invalid_input(self):
        grammar = Grammar(SIMPLE_GRAMMAR_TEXT)
        lexer = Lexer(SIMPLE_TERMINALS_TEXT)
        engine = Earley(grammar)
        tokens = lexer.lex("a a")
        with pytest.raises(ValueError):
            engine.parse(tokens)
