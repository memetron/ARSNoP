"""Integration tests for contextual (parser-driven) lexing."""
from arsnop.grammar import Grammar
from arsnop.grammar.bnf_parser import parse_bnf
from arsnop.lexer import Lexer
from arsnop.parser.shift_reduce import LALR

from .generators.conftest import collect_leaves


# Grammar where "type" is both a keyword and a valid identifier.
#   stmt  ::= TYPE_KW ASSIGN expr
#           | LET ID ASSIGN expr
#   expr  ::= NUM
KEYWORD_ID_BNF = (
    ":GRAMMAR\n"
    "start  ::= stmt ;\n"
    "stmt   ::= TYPE_KW ASSIGN expr | LET ID ASSIGN expr ;\n"
    "expr   ::= NUM ;\n"
    ":TERMINALS\n"
    'TYPE_KW "type" ;\n'
    'LET    "let" ;\n'
    'ASSIGN "=" ;\n'
    "ID     /[a-zA-Z][a-zA-Z0-9_]*/ ;\n"
    "NUM    /[0-9]+/ ;\n"
    "SPC    /[ ]+/ ;\n"
    ".IGNORE SPC ;\n"
)


def _make_automaton():
    spec = parse_bnf(KEYWORD_ID_BNF)
    grammar = Grammar(spec.rules)
    return LALR().generate(grammar), Lexer(spec.terminals, spec.ignored)


class TestContextualLexing:
    def test_type_keyword_in_keyword_position(self):
        """'type = 5' parses via the TYPE_KW branch."""
        automaton, lexer = _make_automaton()
        ast = automaton.parse("type = 5", lexer)
        leaves = collect_leaves(ast)
        assert "type" in leaves
        assert "5" in leaves

    def test_type_as_identifier(self):
        """'let type = 5' succeeds: 'type' is lexed as ID, not TYPE_KW."""
        automaton, lexer = _make_automaton()
        ast = automaton.parse("let type = 5", lexer)
        leaves = collect_leaves(ast)
        assert "type" in leaves
        assert "5" in leaves

    def test_regular_identifier_still_works(self):
        """'let foo = 42' parses normally."""
        automaton, lexer = _make_automaton()
        ast = automaton.parse("let foo = 42", lexer)
        leaves = collect_leaves(ast)
        assert "foo" in leaves
        assert "42" in leaves
