"""Shared fixtures for shift-reduce generator tests."""
from arsnop.grammar import Grammar
from arsnop.lexer import Lexer, Token


SIMPLE_GRAMMAR_TEXT = "start ::= expr\nexpr ::= TOK"
SIMPLE_TERMINALS_TEXT = "TOK a\nSPC [ ]\n.IGNORE\nSPC"

NESTED_GRAMMAR_TEXT = (
    "start ::= list\n"
    "list ::= LP items RP\n"
    "items ::= ITEM SEP items | ITEM"
)
NESTED_TERMINALS_TEXT = "LP \\(\nRP \\)\nSEP ,\nITEM [a-z]+\nSPC [ ]\n.IGNORE\nSPC"

NULLABLE_GRAMMAR_TEXT = "start ::= A B c\nA ::= a | \nB ::= b | "


def parse_with(generator_cls, grammar_text, terminals_text, input_text):
    grammar = Grammar(grammar_text)
    lexer = Lexer(terminals_text)
    automaton = generator_cls().generate(grammar)
    tokens = lexer.lex(input_text)
    return automaton.parse(tokens)


def collect_leaves(ast):
    if not ast.children:
        if isinstance(ast.content, Token):
            return [ast.content.lexeme]
        return [str(ast.content)]
    leaves = []
    for child in ast.children:
        leaves.extend(collect_leaves(child))
    return leaves
