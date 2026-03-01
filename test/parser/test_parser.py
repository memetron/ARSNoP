"""Tests for the parser.parser module (from_file factory)."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from arsnop.ast import AST
from arsnop.grammar import parse_bnf
from arsnop.grammar.grammar import Grammar
from arsnop.lexer import Lexer
from arsnop.lexer.token import Token
from arsnop.parser import from_file
from arsnop.parser.earley.earley import Earley
from arsnop.parser.parsingEngine import ParsingEngine
from arsnop.parser.shift_reduce import SLR


def _collect_nonterminals(ast: AST) -> list[Any]:
    labels: list[Any] = []
    if ast.children:
        labels.append(ast.content if isinstance(ast.content, str) else str(ast.content))
        for child in ast.children:
            labels.extend(_collect_nonterminals(child))
    return labels


class TestFromFile:
    def test_earley_from_file(self):
        parser = from_file("test/resources/simple_english.bnf", parser="earley")
        ast = parser.parse("the quick brown fox jumped over the lazy dog")
        assert ast is not None
        assert "noun" in _collect_nonterminals(ast)

    def test_slr_from_file(self):
        parser = from_file("test/resources/simple_english.bnf", parser="slr")
        ast = parser.parse("the quick brown fox jumped over the lazy dog")
        assert ast is not None

    def test_lr1_from_file(self):
        parser = from_file("test/resources/simple_english.bnf", parser="lr1")
        ast = parser.parse("the quick brown fox jumped over the lazy dog")
        assert ast is not None

    def test_lalr_from_file(self):
        parser = from_file("test/resources/simple_english.bnf", parser="lalr")
        ast = parser.parse("the quick brown fox jumped over the lazy dog")
        assert ast is not None

    def test_lalr_from_file_2(self):
        parser = from_file("test/resources/arithmetic.bnf", parser="lalr")
        ast = parser.parse("1 + ( 2 * 3 )")
        assert ast is not None

    def test_lalr_brute_force_from_file(self):
        parser = from_file("test/resources/simple_english.bnf", parser="lalr_brute_force")
        ast = parser.parse("the quick brown fox jumped over the lazy dog")
        assert ast is not None

    def test_invalid_parser_name(self):
        with pytest.raises(Exception):
            from_file("test/resources/simple_english.bnf", parser="nonexistent")


# ---------------------------------------------------------------------------
# Labeled inline alternatives produce named nodes (not spliced)
# ---------------------------------------------------------------------------

# Grammar: `_ item` is inline, but the `A` alternative carries a label.
# Parsing "a" should yield start -> found(A), not start -> A (spliced).
# Parsing "b" should yield start -> B (spliced, no label).
_LABELED_INLINE_BNF = (
    ":GRAMMAR\n"
    "start ::= item ;\n"
    "_ item ::= A : found | B ;\n"
    ":TERMINALS\n"
    "A /a/ ;\n"
    "B /b/ ;\n"
)


class TestLabeledInline:
    """A label on an inline-rule alternative un-inlines that alternative."""

    def _spec(self) -> tuple[Grammar, Lexer]:
        spec = parse_bnf(_LABELED_INLINE_BNF)
        return Grammar(spec.rules), Lexer(spec.terminals, spec.ignored)

    def test_earley_labeled_alt_creates_named_node(self):
        grammar, lexer = self._spec()
        ast = Earley(grammar).parse("a", lexer)
        # start should have one child: a named "found" node
        assert len(ast.children) == 1
        assert ast.children[0].content == "found"

    def test_earley_unlabeled_alt_still_spliced(self):
        grammar, lexer = self._spec()
        ast = Earley(grammar).parse("b", lexer)
        # start should have one child: the B token directly (spliced)
        assert len(ast.children) == 1
        assert isinstance(ast.children[0].content, Token)
        assert ast.children[0].content.token == "B"

    def test_slr_labeled_alt_creates_named_node(self):
        grammar, lexer = self._spec()
        ast = SLR().generate(grammar).parse("a", lexer)
        assert len(ast.children) == 1
        assert ast.children[0].content == "found"

    def test_slr_unlabeled_alt_still_spliced(self):
        grammar, lexer = self._spec()
        ast = SLR().generate(grammar).parse("b", lexer)
        assert len(ast.children) == 1
        assert isinstance(ast.children[0].content, Token)
        assert ast.children[0].content.token == "B"


# ---------------------------------------------------------------------------
# Inline token tree omission
# ---------------------------------------------------------------------------

# Grammar: start ::= A "," B  (the comma literal is an inline terminal)
_INLINE_BNF = (
    ":GRAMMAR\n"
    "start ::= A \",\" B ;\n"
    ":TERMINALS\n"
    "A /[a-z]+/ ;\n"
    "B /[0-9]+/ ;\n"
    "WS /[ ]+/ ;\n"
    ".IGNORE WS ;\n"
)


def _leaf_tokens(ast: AST) -> list[Token]:
    """Collect all leaf Token nodes from the AST, depth-first."""
    if isinstance(ast.content, Token):
        return [ast.content]
    result: list[Token] = []
    for child in ast.children:
        result.extend(_leaf_tokens(child))
    return result


class TestInlineTokenTree:
    """Inline terminals (anonymous literals in rules) are omitted from the AST."""

    def _parse(self, parser_engine: Callable[[Grammar], ParsingEngine]) -> AST:
        spec = parse_bnf(_INLINE_BNF)
        grammar = Grammar(spec.rules)
        lexer = Lexer(spec.terminals, spec.ignored)
        return parser_engine(grammar).parse("foo, 42", lexer)

    def test_earley_inline_token_absent(self):
        ast = self._parse(Earley)
        leaves = _leaf_tokens(ast)
        assert not any(t.token.startswith("_INLINE_") for t in leaves)

    def test_earley_non_inline_tokens_present(self):
        ast = self._parse(Earley)
        leaves = _leaf_tokens(ast)
        token_types = [t.token for t in leaves]
        assert "A" in token_types
        assert "B" in token_types

    def test_earley_exactly_two_leaves(self):
        ast = self._parse(Earley)
        assert len(_leaf_tokens(ast)) == 2

    def test_slr_inline_token_absent(self):
        spec = parse_bnf(_INLINE_BNF)
        grammar = Grammar(spec.rules)
        lexer = Lexer(spec.terminals, spec.ignored)
        ast = SLR().generate(grammar).parse("foo, 42", lexer)
        leaves = _leaf_tokens(ast)
        assert not any(t.token.startswith("_INLINE_") for t in leaves)

    def test_slr_exactly_two_leaves(self):
        spec = parse_bnf(_INLINE_BNF)
        grammar = Grammar(spec.rules)
        lexer = Lexer(spec.terminals, spec.ignored)
        ast = SLR().generate(grammar).parse("foo, 42", lexer)
        assert len(_leaf_tokens(ast)) == 2
