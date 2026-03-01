"""Tests for Earley.trace()."""

from arsnop.grammar import Grammar
from arsnop.grammar.bnf_parser import parse_bnf
from arsnop.lexer import Lexer
from arsnop.ast import AST
from arsnop.lexer.token import Token
from arsnop.parser.earley import Earley, EarleyTrace, EarleyColumn, TracedEarleyItem


BNF_TEXT = (
    ":GRAMMAR\n"
    "start ::= expr ;\n"
    "expr ::= expr PLUS term | term ;\n"
    "term ::= NUM ;\n"
    ":TERMINALS\n"
    "PLUS /\\+/ ;\n"
    "NUM /[0-9]+/ ;\n"
    "SPC /[ ]/ ;\n"
    ".IGNORE SPC ;\n"
)

_SPEC = parse_bnf(BNF_TEXT)
_LEXER = Lexer(_SPEC.terminals, _SPEC.ignored)


def _collect_leaves(node: AST) -> list[str]:
    if not node.children:
        content = node.content
        return [content.lexeme if isinstance(content, Token) else str(content)]
    leaves: list[str] = []
    for child in node.children:
        leaves.extend(_collect_leaves(child))
    return leaves


class TestTraceReturnType:
    def test_returns_earley_trace(self):
        grammar = Grammar(_SPEC.rules)
        result = Earley.trace(grammar, "1 + 2", _LEXER)
        assert isinstance(result, EarleyTrace)

    def test_chart_contains_columns(self):
        grammar = Grammar(_SPEC.rules)
        result = Earley.trace(grammar, "1", _LEXER)
        assert all(isinstance(c, EarleyColumn) for c in result.chart)

    def test_items_are_traced(self):
        grammar = Grammar(_SPEC.rules)
        result = Earley.trace(grammar, "1", _LEXER)
        for col in result.chart:
            assert all(isinstance(it, TracedEarleyItem) for it in col.items)


class TestTraceChart:
    def test_chart_length(self):
        grammar = Grammar(_SPEC.rules)
        result = Earley.trace(grammar, "1 + 2", _LEXER)
        # chart has len(tokens) + 1 columns; "1 + 2" → 3 tokens
        assert len(result.chart) == 4

    def test_first_column_has_no_token(self):
        grammar = Grammar(_SPEC.rules)
        result = Earley.trace(grammar, "1", _LEXER)
        assert result.chart[0].token is None

    def test_subsequent_columns_have_tokens(self):
        grammar = Grammar(_SPEC.rules)
        result = Earley.trace(grammar, "1 + 2", _LEXER)
        for i, col in enumerate(result.chart):
            if i == 0:
                assert col.token is None
            else:
                assert col.token is not None

    def test_column_indices(self):
        grammar = Grammar(_SPEC.rules)
        result = Earley.trace(grammar, "1 + 2", _LEXER)
        for i, col in enumerate(result.chart):
            assert col.index == i


class TestTraceOperations:
    def test_operations_are_valid(self):
        grammar = Grammar(_SPEC.rules)
        result = Earley.trace(grammar, "1 + 2", _LEXER)
        valid_ops = {"init", "predict", "scan", "complete"}
        for col in result.chart:
            for item in col.items:
                assert item.operation in valid_ops

    def test_first_column_has_init(self):
        grammar = Grammar(_SPEC.rules)
        result = Earley.trace(grammar, "1", _LEXER)
        ops = {it.operation for it in result.chart[0].items}
        assert "init" in ops

    def test_has_predict_items(self):
        grammar = Grammar(_SPEC.rules)
        result = Earley.trace(grammar, "1", _LEXER)
        all_ops = {it.operation for col in result.chart for it in col.items}
        assert "predict" in all_ops

    def test_has_scan_items(self):
        grammar = Grammar(_SPEC.rules)
        result = Earley.trace(grammar, "1", _LEXER)
        # Columns after 0 should have scanned items
        all_ops = set()
        for col in result.chart[1:]:
            for it in col.items:
                all_ops.add(it.operation)
        assert "scan" in all_ops


class TestTraceASTConsistency:
    def test_ast_leaves_match_parse(self):
        grammar = Grammar(_SPEC.rules)
        trace_result = Earley.trace(grammar, "1 + 2", _LEXER)
        parse_result = Earley(grammar).parse("1 + 2", _LEXER)
        assert trace_result.ast is not None
        assert _collect_leaves(trace_result.ast) == _collect_leaves(parse_result)

    def test_no_error_on_success(self):
        grammar = Grammar(_SPEC.rules)
        result = Earley.trace(grammar, "1", _LEXER)
        assert result.error is None
        assert result.ast is not None

    def test_tokens_preserved(self):
        grammar = Grammar(_SPEC.rules)
        result = Earley.trace(grammar, "1 + 2", _LEXER)
        # "1 + 2" produces 3 tokens (NUM, PLUS, NUM)
        assert len(result.tokens) == 3


class TestTraceError:
    def test_error_on_unexpected_token(self):
        grammar = Grammar(_SPEC.rules)
        # "+" cannot be lexed as valid in the initial state (only NUM is expected)
        result = Earley.trace(grammar, "+", _LEXER)
        assert result.ast is None
        assert result.error is not None

    def test_error_has_partial_chart(self):
        grammar = Grammar(_SPEC.rules)
        # "1 2": after lexing "1", PLUS is the only valid next terminal
        # so "2" cannot be lexed in that state → lex error after column 1 built
        result = Earley.trace(grammar, "1 2", _LEXER)
        assert result.ast is None
        assert result.error is not None
        # Should have at least column 0 and column 1
        assert len(result.chart) >= 2
