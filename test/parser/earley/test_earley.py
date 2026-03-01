"""Tests for the Earley parser."""
import pytest

from arsnop.grammar import Grammar
from arsnop.grammar.bnf_parser import parse_bnf
from arsnop.lexer import Lexer, Token
from arsnop.parser.earley import Earley


SIMPLE_BNF = (
    ":GRAMMAR\n"
    "start ::= expr ;\n"
    "expr ::= TOK ;\n"
    ":TERMINALS\n"
    'TOK "a" ;\n'
    "SPC /[ ]/ ;\n"
    ".IGNORE SPC ;\n"
)

ARITH_BNF = (
    ":GRAMMAR\n"
    "start ::= expr ;\n"
    "expr ::= expr OP NUM | NUM ;\n"
    ":TERMINALS\n"
    "OP /[+\\-]/ ;\n"
    "NUM /[0-9]+/ ;\n"
    "SPC /[ ]/ ;\n"
    ".IGNORE SPC ;\n"
)

NESTED_BNF = (
    ":GRAMMAR\n"
    "start ::= list ;\n"
    "list ::= LP items RP ;\n"
    "items ::= ITEM SEP items | ITEM ;\n"
    ":TERMINALS\n"
    "LP /\\(/ ;\n"
    "RP /\\)/ ;\n"
    'SEP "," ;\n'
    "ITEM /[a-z]+/ ;\n"
    "SPC /[ ]/ ;\n"
    ".IGNORE SPC ;\n"
)


def _parse(bnf_text, input_text):
    spec = parse_bnf(bnf_text)
    grammar = Grammar(spec.rules)
    lexer = Lexer(spec.terminals, spec.ignored)
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
        ast = _parse(SIMPLE_BNF, "a")
        assert ast is not None
        assert _collect_leaves(ast) == ["a"]

    def test_parse_arithmetic(self):
        ast = _parse(ARITH_BNF, "1 + 2")
        assert ast is not None
        assert _collect_leaves(ast) == ["1", "+", "2"]

    def test_parse_nested(self):
        ast = _parse(NESTED_BNF, "(foo,bar,baz)")
        assert ast is not None
        assert _collect_leaves(ast) == ["(", "foo", ",", "bar", ",", "baz", ")"]

    def test_reject_invalid_input(self):
        spec = parse_bnf(SIMPLE_BNF)
        grammar = Grammar(spec.rules)
        lexer = Lexer(spec.terminals, spec.ignored)
        engine = Earley(grammar)
        tokens = lexer.lex("a a")
        with pytest.raises(ValueError):
            engine.parse(tokens)


_EBNF_BNF = (
    ":GRAMMAR\n"
    "start ::= a* ;\n"
    "a ::= A ;\n"
    ":TERMINALS\n"
    "A /A/ ;\n"
)


def _parse_ebnf(input_text: str):
    spec = parse_bnf(_EBNF_BNF)
    return Earley(Grammar(spec.rules)).parse(Lexer(spec.terminals, spec.ignored).lex(input_text))


class TestEarleyModifierInlining:
    """EBNF-generated aux rule nodes should be absent from the Earley AST."""

    def test_star_empty_start_has_no_children(self):
        ast = _parse_ebnf("")
        assert ast.content == "start"
        assert ast.children == []

    def test_star_single_child_directly_on_start(self):
        ast = _parse_ebnf("A")
        assert ast.content == "start"
        assert len(ast.children) == 1
        assert ast.children[0].content == "a"

    def test_star_multiple_children_directly_on_start(self):
        ast = _parse_ebnf("AAA")
        assert ast.content == "start"
        assert len(ast.children) == 3

    def test_star_no_aux_node_in_tree(self):
        ast = _parse_ebnf("AAA")
        assert all(child.content != "_a_star" for child in ast.children)

    def test_star_children_are_a_nodes(self):
        ast = _parse_ebnf("AAA")
        assert all(child.content == "a" for child in ast.children)
