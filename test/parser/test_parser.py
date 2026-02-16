"""Tests for the parser.parser module (from_file factory)."""
import pytest

from src.parser import from_file


def _collect_nonterminals(ast):
    labels = []
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
