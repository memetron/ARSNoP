"""Tests for shift-reduce parser generators."""
from src.grammar import Grammar
from src.lexer import Lexer, Token
from src.parser.earley import Earley
from src.parser.shift_reduce import LR0, LR1, SLR, LALR, LALR_Brute_Force


SIMPLE_GRAMMAR_TEXT = "start ::= expr\nexpr ::= TOK"
SIMPLE_TERMINALS_TEXT = "TOK a\nSPC [ ]\n.IGNORE\nSPC"

NESTED_GRAMMAR_TEXT = (
    "start ::= list\n"
    "list ::= LP items RP\n"
    "items ::= ITEM SEP items | ITEM"
)
NESTED_TERMINALS_TEXT = "LP \\(\nRP \\)\nSEP ,\nITEM [a-z]+\nSPC [ ]\n.IGNORE\nSPC"

ALL_GENERATORS = [SLR, LR1, LALR, LALR_Brute_Force]


def _parse_with(generator_cls, grammar_text, terminals_text, input_text):
    grammar = Grammar(grammar_text)
    lexer = Lexer(terminals_text)
    automaton = generator_cls().generate(grammar)
    tokens = lexer.lex(input_text)
    return automaton.parse(tokens)


def _collect_leaves(ast):
    if not ast.children:
        if isinstance(ast.content, Token):
            return [ast.content.lexeme]
        return [str(ast.content)]
    leaves = []
    for child in ast.children:
        leaves.extend(_collect_leaves(child))
    return leaves


# ===================================================================
# Per-generator correctness
# ===================================================================

class TestSLRGenerator:
    def test_parse_simple(self):
        ast = _parse_with(SLR, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast is not None
        assert _collect_leaves(ast) == ["a"]

    def test_parse_nested(self):
        ast = _parse_with(SLR, NESTED_GRAMMAR_TEXT, NESTED_TERMINALS_TEXT, "(foo,bar)")
        assert ast is not None
        assert _collect_leaves(ast) == ["(", "foo", ",", "bar", ")"]

    def test_ast_structure(self):
        ast = _parse_with(SLR, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast.content == "start"
        assert len(ast.children) == 1
        assert ast.children[0].content == "expr"


class TestLR1Generator:
    def test_parse_simple(self):
        ast = _parse_with(LR1, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast is not None
        assert _collect_leaves(ast) == ["a"]

    def test_parse_nested(self):
        ast = _parse_with(LR1, NESTED_GRAMMAR_TEXT, NESTED_TERMINALS_TEXT, "(foo,bar)")
        assert ast is not None
        assert _collect_leaves(ast) == ["(", "foo", ",", "bar", ")"]

    def test_ast_structure(self):
        ast = _parse_with(LR1, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast.content == "start"
        assert len(ast.children) == 1
        assert ast.children[0].content == "expr"


class TestLALRGenerator:
    def test_parse_simple(self):
        ast = _parse_with(LALR, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast is not None
        assert _collect_leaves(ast) == ["a"]

    def test_parse_nested(self):
        ast = _parse_with(LALR, NESTED_GRAMMAR_TEXT, NESTED_TERMINALS_TEXT, "(foo,bar)")
        assert ast is not None
        assert _collect_leaves(ast) == ["(", "foo", ",", "bar", ")"]

    def test_ast_structure(self):
        ast = _parse_with(LALR, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast.content == "start"
        assert len(ast.children) == 1
        assert ast.children[0].content == "expr"


class TestLALRBruteForceGenerator:
    def test_parse_simple(self):
        ast = _parse_with(LALR_Brute_Force, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast is not None
        assert _collect_leaves(ast) == ["a"]

    def test_parse_nested(self):
        ast = _parse_with(LALR_Brute_Force, NESTED_GRAMMAR_TEXT, NESTED_TERMINALS_TEXT, "(foo,bar)")
        assert ast is not None
        assert _collect_leaves(ast) == ["(", "foo", ",", "bar", ")"]

    def test_ast_structure(self):
        ast = _parse_with(LALR_Brute_Force, SIMPLE_GRAMMAR_TEXT, SIMPLE_TERMINALS_TEXT, "a")
        assert ast.content == "start"
        assert len(ast.children) == 1
        assert ast.children[0].content == "expr"


class TestGeneratorConsistency:
    def test_all_generators_agree_on_leaves(self):
        input_text = "(foo,bar,baz)"
        results = {}
        for gen_cls in ALL_GENERATORS:
            ast = _parse_with(gen_cls, NESTED_GRAMMAR_TEXT, NESTED_TERMINALS_TEXT, input_text)
            results[gen_cls.__name__] = _collect_leaves(ast)

        values = list(results.values())
        for name, leaves in results.items():
            assert leaves == values[0], (
                f"{name} produced different leaves: {leaves} vs {values[0]}"
            )

    def test_earley_agrees_with_shift_reduce(self):
        input_text = "(foo,bar)"
        grammar = Grammar(NESTED_GRAMMAR_TEXT)
        lexer = Lexer(NESTED_TERMINALS_TEXT)

        earley_ast = Earley(grammar).parse(lexer.lex(input_text))
        slr_ast = _parse_with(SLR, NESTED_GRAMMAR_TEXT, NESTED_TERMINALS_TEXT, input_text)
        assert _collect_leaves(earley_ast) == _collect_leaves(slr_ast)


# ===================================================================
# Bug regressions
# ===================================================================

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
