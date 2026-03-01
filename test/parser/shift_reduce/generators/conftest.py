"""Shared fixtures for shift-reduce generator tests."""
from arsnop.grammar import Grammar
from arsnop.grammar.bnf_parser import parse_bnf
from arsnop.lexer import Lexer, Token


SIMPLE_BNF = (
    ":GRAMMAR\n"
    "start ::= expr ;\n"
    "expr ::= TOK ;\n"
    ":TERMINALS\n"
    'TOK "a" ;\n'
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

NULLABLE_BNF = (
    ":GRAMMAR\n"
    "start ::= A B c ;\n"
    "A ::= a | ;\n"
    "B ::= b | ;\n"
    ":TERMINALS\n"
)


def parse_with(generator_cls, bnf_text, input_text):
    spec = parse_bnf(bnf_text)
    grammar = Grammar(spec.rules)
    lexer = Lexer(spec.terminals, spec.ignored)
    automaton = generator_cls().generate(grammar)
    return automaton.parse(input_text, lexer)


def collect_leaves(ast):
    if not ast.children:
        if isinstance(ast.content, Token):
            return [ast.content.lexeme]
        return [str(ast.content)]
    leaves = []
    for child in ast.children:
        leaves.extend(collect_leaves(child))
    return leaves
