"""Cross-generator consistency tests."""
from arsnop.grammar import Grammar
from arsnop.grammar.bnf_parser import parse_bnf
from arsnop.lexer import Lexer
from arsnop.parser.earley import Earley
from arsnop.parser.shift_reduce import SLR, LR1, LALR, LALR_Brute_Force

from .conftest import (
    NESTED_BNF,
    parse_with,
    collect_leaves,
)

ALL_GENERATORS = [SLR, LR1, LALR, LALR_Brute_Force]


class TestGeneratorConsistency:
    def test_all_generators_agree_on_leaves(self):
        input_text = "(foo,bar,baz)"
        results = {}
        for gen_cls in ALL_GENERATORS:
            ast = parse_with(gen_cls, NESTED_BNF, input_text)
            results[gen_cls.__name__] = collect_leaves(ast)

        values = list(results.values())
        for name, leaves in results.items():
            assert leaves == values[0], (
                f"{name} produced different leaves: {leaves} vs {values[0]}"
            )

    def test_earley_agrees_with_shift_reduce(self):
        input_text = "(foo,bar)"
        spec = parse_bnf(NESTED_BNF)
        grammar = Grammar(spec.rules)
        lexer = Lexer(spec.terminals, spec.ignored)

        earley_ast = Earley(grammar).parse(input_text, lexer)
        slr_ast = parse_with(SLR, NESTED_BNF, input_text)
        assert collect_leaves(earley_ast) == collect_leaves(slr_ast)
