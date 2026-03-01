"""Tests for arsnop/grammar/bnf_parser.py."""

import pytest

from arsnop.grammar import (
    Rhs,
    BnfSpec,
    BnfSpecTransformer,
    RuleSpec,
    TerminalSpec,
    parse_bnf,
    parse_bnf_ast,
)
from arsnop.ast import AST


# ---------------------------------------------------------------------------
# parse_bnf
# ---------------------------------------------------------------------------

class TestParseBnf:
    def test_minimal_valid(self):
        text = ":GRAMMAR\nstart ::= A ;\n:TERMINALS\nA /a/ ;\n"
        spec = parse_bnf(text)
        assert isinstance(spec, BnfSpec)
        assert len(spec.rules) == 1
        assert len(spec.terminals) == 1

    def test_rule_structure(self):
        text = ":GRAMMAR\nstart ::= A ;\n:TERMINALS\nA /a/ ;\n"
        spec = parse_bnf(text)
        rule = spec.rules[0]
        assert isinstance(rule, RuleSpec)
        assert rule.lhs == "start"
        assert rule.alternatives == (Rhs(("A",)),)

    def test_terminal_structure(self):
        text = ":GRAMMAR\nstart ::= A ;\n:TERMINALS\nA /a/ ;\n"
        spec = parse_bnf(text)
        term = spec.terminals[0]
        assert isinstance(term, TerminalSpec)
        assert term.name == "A"
        assert term.pattern == "a"

    def test_multiple_rules(self):
        text = ":GRAMMAR\nstart ::= expr ;\nexpr ::= NUM ;\n:TERMINALS\nNUM /[0-9]+/ ;\n"
        spec = parse_bnf(text)
        assert len(spec.rules) == 2
        lhs_list = [r.lhs for r in spec.rules]
        assert "start" in lhs_list
        assert "expr" in lhs_list

    def test_multiple_alternatives(self):
        text = ":GRAMMAR\nexpr ::= NUM | ID ;\n:TERMINALS\nNUM /[0-9]+/ ;\nID /[a-z]+/ ;\n"
        spec = parse_bnf(text)
        assert len(spec.rules) == 1
        rule = spec.rules[0]
        assert len(rule.alternatives) == 2
        symbols = {alt.symbols for alt in rule.alternatives}
        assert ("NUM",) in symbols
        assert ("ID",) in symbols

    def test_nullable_alternative(self):
        text = ":GRAMMAR\nA ::= a | ;\n:TERMINALS\na /a/ ;\n"
        spec = parse_bnf(text)
        rule = spec.rules[0]
        # one alternative with 'a', one empty
        all_syms = {alt.symbols for alt in rule.alternatives}
        assert ("a",) in all_syms
        assert () in all_syms

    def test_terminal_pattern_with_spaces(self):
        text = ":GRAMMAR\nstart ::= SPC ;\n:TERMINALS\nSPC /[ \\t\\n\\r]+/ ;\n"
        spec = parse_bnf(text)
        assert len(spec.terminals) == 1
        assert spec.terminals[0].name == "SPC"
        assert spec.terminals[0].pattern == "[ \\t\\n\\r]+"

    def test_ignore_section(self):
        text = ":GRAMMAR\nstart ::= NUM ;\n:TERMINALS\nNUM /[0-9]+/ ;\nSPC /[ ]+/ ;\n.IGNORE SPC ;\n"
        spec = parse_bnf(text)
        assert "SPC" in spec.ignored

    def test_absent_ignore_section(self):
        text = ":GRAMMAR\nstart ::= NUM ;\n:TERMINALS\nNUM /[0-9]+/ ;\n"
        spec = parse_bnf(text)
        assert spec.ignored == ()

    def test_missing_grammar_keyword_raises(self):
        with pytest.raises((ValueError, Exception)):
            parse_bnf(":TERMINALS\nA /a/ ;\n")

    def test_missing_terminals_keyword_raises(self):
        with pytest.raises((ValueError, Exception)):
            parse_bnf(":GRAMMAR\nstart ::= A ;\n")

    def test_empty_string_raises(self):
        with pytest.raises((ValueError, Exception)):
            parse_bnf("")

    def test_full_file(self):
        text = (
            ":GRAMMAR\n"
            "start ::= expr ;\n"
            "expr ::= expr OP NUM | NUM ;\n"
            ":TERMINALS\n"
            "NUM /[0-9]+/ ;\n"
            "OP /[+\\-*\\/]/ ;\n"
            "SPC /[ ]+/ ;\n"
            ".IGNORE SPC ;\n"
        )
        spec = parse_bnf(text)
        assert len(spec.rules) == 2
        assert len(spec.terminals) == 3
        assert "SPC" in spec.ignored

    def test_literal_terminal(self):
        text = ":GRAMMAR\nstart ::= KW ;\n:TERMINALS\nKW \"and\" ;\n"
        spec = parse_bnf(text)
        assert spec.terminals[0].name == "KW"
        assert spec.terminals[0].pattern == "and"


# ---------------------------------------------------------------------------
# parse_bnf_ast + BnfSpecTransformer
# ---------------------------------------------------------------------------

class TestParseBnfAst:
    _SIMPLE = ":GRAMMAR\nstart ::= A ;\n:TERMINALS\nA /a/ ;\n"

    def test_returns_ast(self):
        tree = parse_bnf_ast(self._SIMPLE)
        assert isinstance(tree, AST)

    def test_root_is_bnf_file(self):
        tree = parse_bnf_ast(self._SIMPLE)
        assert tree.content == "bnf_file"

    def test_has_four_children(self):
        # bnf_file ::= GRAMMAR_KW rules_section TERMINALS_KW terminals_section
        tree = parse_bnf_ast(self._SIMPLE)
        assert len(tree.children) == 4

    def test_second_child_is_rules_section(self):
        # children: [GRAMMAR_KW_token, rules_section, TERMINALS_KW_token, terminals_section]
        tree = parse_bnf_ast(self._SIMPLE)
        assert tree.children[1].content == "rules_section"

    def test_fourth_child_is_terminals_section(self):
        tree = parse_bnf_ast(self._SIMPLE)
        assert tree.children[3].content == "terminals_section"

    def test_rule_lhs_token(self):
        tree = parse_bnf_ast(self._SIMPLE)
        # rules_section (index 1) has children: [empty rules_section, rule]
        rules_section = tree.children[1]
        rule = rules_section.children[1]
        assert rule.content == "rule"
        # First child of 'rule' is a leaf Token node for the LHS.
        lhs_node = rule.children[0]
        from arsnop.lexer.token import Token as Tok
        assert isinstance(lhs_node.content, Tok)
        assert lhs_node.content.lexeme == "start"

    def test_alternatives_node(self):
        tree = parse_bnf_ast(self._SIMPLE)
        rules_section = tree.children[1]
        rule = rules_section.children[1]
        # rule ::= ID ARROW alternatives SEMI — alternatives is at index 2
        alts = rule.children[2]
        assert alts.content == "alternatives"
        assert len(alts.children) == 1
        assert alts.children[0].content == "alternative"

    def test_terminal_def_structure(self):
        tree = parse_bnf_ast(self._SIMPLE)
        # terminals_section (index 3) has children: [empty terminals_section, terminal_def]
        terminals_section = tree.children[3]
        term_def = terminals_section.children[1]
        assert term_def.content == "terminal_def"
        # terminal_def ::= ID REGEX SEMI — three children
        assert len(term_def.children) == 3
        # children[1] is the REGEX or QUOTED pattern token
        from arsnop.lexer.token import Token as Tok
        assert isinstance(term_def.children[1].content, Tok)
        assert term_def.children[1].content.token in ("QUOTED", "REGEX")

    def test_transformer_roundtrip(self):
        text = (
            ":GRAMMAR\n"
            "start ::= expr ;\n"
            "expr ::= expr OP NUM | NUM ;\n"
            ":TERMINALS\n"
            "NUM /[0-9]+/ ;\n"
            "OP /[+\\-*\\/]/ ;\n"
            "SPC /[ ]+/ ;\n"
            ".IGNORE SPC ;\n"
        )
        assert BnfSpecTransformer().transform(parse_bnf_ast(text)) == parse_bnf(text)

    def test_transformer_simple(self):
        tree = parse_bnf_ast(self._SIMPLE)
        result = BnfSpecTransformer().transform(tree)
        assert isinstance(result, BnfSpec)
        assert result == parse_bnf(self._SIMPLE)

    def test_transformer_nullable_alt(self):
        text = ":GRAMMAR\nA ::= a | ;\n:TERMINALS\na /a/ ;\n"
        assert BnfSpecTransformer().transform(parse_bnf_ast(text)) == parse_bnf(text)

    def test_transformer_pattern_with_spaces(self):
        text = ":GRAMMAR\nstart ::= SPC ;\n:TERMINALS\nSPC /[ \\t]+/ ;\n"
        result = BnfSpecTransformer().transform(parse_bnf_ast(text))
        assert isinstance(result, BnfSpec)
        assert result.terminals[0].pattern == "[ \\t]+"

    def test_empty_string_raises(self):
        with pytest.raises((ValueError, Exception)):
            parse_bnf_ast("")
