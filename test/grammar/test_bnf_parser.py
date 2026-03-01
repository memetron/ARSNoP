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
from arsnop.grammar.bnf_types import InlineType
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
        # rule ::= optional_inline ID ARROW alternatives SEMI
        # First child is optional_inline; second child is the ID token.
        lhs_node = rule.children[1]
        from arsnop.lexer.token import Token as Tok
        assert isinstance(lhs_node.content, Tok)
        assert lhs_node.content.lexeme == "start"

    def test_alternatives_node(self):
        tree = parse_bnf_ast(self._SIMPLE)
        rules_section = tree.children[1]
        rule = rules_section.children[1]
        # rule ::= optional_inline ID ARROW alternatives SEMI — alternatives is at index 3
        alts = rule.children[3]
        assert alts.content == "alternatives"
        # alternatives ::= alternative optional_label — two children
        assert len(alts.children) == 2
        assert alts.children[0].content == "alternative"
        assert alts.children[1].content == "optional_label"

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


# ---------------------------------------------------------------------------
# EBNF modifier desugaring
# ---------------------------------------------------------------------------

class TestModifiers:
    """BnfSpecTransformer desugars ?, *, + into auxiliary BNF rules."""

    def _aux(self, spec: BnfSpec, name: str) -> RuleSpec:
        return next(r for r in spec.rules if r.lhs == name)

    def test_optional_adds_aux_rule(self):
        text = ":GRAMMAR\nstart ::= A? ;\n:TERMINALS\nA /a/ ;\n"
        spec = parse_bnf(text)
        assert any(r.lhs == "_A_opt" for r in spec.rules)

    def test_optional_aux_rule_alts(self):
        text = ":GRAMMAR\nstart ::= A? ;\n:TERMINALS\nA /a/ ;\n"
        spec = parse_bnf(text)
        aux = self._aux(spec, "_A_opt")
        assert Rhs(("A",)) in aux.alternatives
        assert Rhs(()) in aux.alternatives

    def test_optional_replaces_symbol(self):
        text = ":GRAMMAR\nstart ::= A? ;\n:TERMINALS\nA /a/ ;\n"
        spec = parse_bnf(text)
        start = self._aux(spec, "start")
        assert start.alternatives == (Rhs(("_A_opt",)),)

    def test_star_adds_aux_rule(self):
        text = ":GRAMMAR\nstart ::= A* ;\n:TERMINALS\nA /a/ ;\n"
        spec = parse_bnf(text)
        assert any(r.lhs == "_A_star" for r in spec.rules)

    def test_star_aux_rule_alts(self):
        text = ":GRAMMAR\nstart ::= A* ;\n:TERMINALS\nA /a/ ;\n"
        spec = parse_bnf(text)
        aux = self._aux(spec, "_A_star")
        assert Rhs(("_A_star", "A")) in aux.alternatives
        assert Rhs(()) in aux.alternatives

    def test_star_replaces_symbol(self):
        text = ":GRAMMAR\nstart ::= A* ;\n:TERMINALS\nA /a/ ;\n"
        spec = parse_bnf(text)
        start = self._aux(spec, "start")
        assert start.alternatives == (Rhs(("_A_star",)),)

    def test_plus_adds_aux_rule(self):
        text = ":GRAMMAR\nstart ::= A+ ;\n:TERMINALS\nA /a/ ;\n"
        spec = parse_bnf(text)
        assert any(r.lhs == "_A_plus" for r in spec.rules)

    def test_plus_aux_rule_alts(self):
        text = ":GRAMMAR\nstart ::= A+ ;\n:TERMINALS\nA /a/ ;\n"
        spec = parse_bnf(text)
        aux = self._aux(spec, "_A_plus")
        assert Rhs(("_A_plus", "A")) in aux.alternatives
        assert Rhs(("A",)) in aux.alternatives

    def test_plus_replaces_symbol(self):
        text = ":GRAMMAR\nstart ::= A+ ;\n:TERMINALS\nA /a/ ;\n"
        spec = parse_bnf(text)
        start = self._aux(spec, "start")
        assert start.alternatives == (Rhs(("_A_plus",)),)

    def test_deduplication(self):
        """A? appearing in two rules generates only one _A_opt rule."""
        text = ":GRAMMAR\nfoo ::= A? ;\nbar ::= A? ;\n:TERMINALS\nA /a/ ;\n"
        spec = parse_bnf(text)
        assert sum(1 for r in spec.rules if r.lhs == "_A_opt") == 1

    def test_multiple_modifiers_in_one_alt(self):
        text = ":GRAMMAR\nstart ::= A? B* ;\n:TERMINALS\nA /a/ ;\nB /b/ ;\n"
        spec = parse_bnf(text)
        start = self._aux(spec, "start")
        assert start.alternatives == (Rhs(("_A_opt", "_B_star")),)


# ---------------------------------------------------------------------------
# EBNF grouping
# ---------------------------------------------------------------------------

class TestGrouping:
    """BnfSpecTransformer desugars (...) groups into inline auxiliary rules."""

    def _aux(self, spec: BnfSpec, name: str) -> RuleSpec:
        return next(r for r in spec.rules if r.lhs == name)

    def _group_rules(self, spec: BnfSpec) -> list[RuleSpec]:
        return [r for r in spec.rules if r.lhs.startswith("_group_")]

    def test_bare_group_creates_aux_rule(self):
        text = ":GRAMMAR\nstart ::= (A B) ;\n:TERMINALS\nA /a/ ;\nB /b/ ;\n"
        spec = parse_bnf(text)
        groups = self._group_rules(spec)
        assert len(groups) == 1

    def test_bare_group_aux_rule_is_inline(self):
        text = ":GRAMMAR\nstart ::= (A B) ;\n:TERMINALS\nA /a/ ;\nB /b/ ;\n"
        spec = parse_bnf(text)
        group = self._group_rules(spec)[0]
        assert group.inline == InlineType.INLINE

    def test_bare_group_aux_rule_alternatives(self):
        text = ":GRAMMAR\nstart ::= (A B) ;\n:TERMINALS\nA /a/ ;\nB /b/ ;\n"
        spec = parse_bnf(text)
        group = self._group_rules(spec)[0]
        assert group.alternatives == (Rhs(("A", "B")),)

    def test_bare_group_replaces_symbol_in_parent(self):
        text = ":GRAMMAR\nstart ::= (A B) ;\n:TERMINALS\nA /a/ ;\nB /b/ ;\n"
        spec = parse_bnf(text)
        group_name = self._group_rules(spec)[0].lhs
        start = self._aux(spec, "start")
        assert start.alternatives == (Rhs((group_name,)),)

    def test_group_with_optional_modifier(self):
        text = ":GRAMMAR\nstart ::= (A B)? ;\n:TERMINALS\nA /a/ ;\nB /b/ ;\n"
        spec = parse_bnf(text)
        groups = self._group_rules(spec)
        assert len(groups) == 1
        group_name = groups[0].lhs
        opt_name = f"_{group_name}_opt"
        assert any(r.lhs == opt_name for r in spec.rules)

    def test_group_with_star_modifier(self):
        text = ":GRAMMAR\nstart ::= (A B)* ;\n:TERMINALS\nA /a/ ;\nB /b/ ;\n"
        spec = parse_bnf(text)
        group_name = self._group_rules(spec)[0].lhs
        star_name = f"_{group_name}_star"
        star = self._aux(spec, star_name)
        assert Rhs((star_name, group_name)) in star.alternatives
        assert Rhs(()) in star.alternatives

    def test_group_with_plus_modifier(self):
        text = ":GRAMMAR\nstart ::= (A B)+ ;\n:TERMINALS\nA /a/ ;\nB /b/ ;\n"
        spec = parse_bnf(text)
        group_name = self._group_rules(spec)[0].lhs
        plus_name = f"_{group_name}_plus"
        plus = self._aux(spec, plus_name)
        assert Rhs((plus_name, group_name)) in plus.alternatives
        assert Rhs((group_name,)) in plus.alternatives

    def test_group_with_alternatives(self):
        text = ":GRAMMAR\nstart ::= (A | B)* ;\n:TERMINALS\nA /a/ ;\nB /b/ ;\n"
        spec = parse_bnf(text)
        group = self._group_rules(spec)[0]
        assert Rhs(("A",)) in group.alternatives
        assert Rhs(("B",)) in group.alternatives

    def test_multiple_groups_get_distinct_names(self):
        text = ":GRAMMAR\nstart ::= (A B) (C D) ;\n:TERMINALS\nA /a/ ;\nB /b/ ;\nC /c/ ;\nD /d/ ;\n"
        spec = parse_bnf(text)
        groups = self._group_rules(spec)
        assert len(groups) == 2
        assert groups[0].lhs != groups[1].lhs

    def test_nested_group(self):
        text = ":GRAMMAR\nstart ::= ((A B) C)? ;\n:TERMINALS\nA /a/ ;\nB /b/ ;\nC /c/ ;\n"
        spec = parse_bnf(text)
        groups = self._group_rules(spec)
        assert len(groups) == 2


# ---------------------------------------------------------------------------
# Inline rules
# ---------------------------------------------------------------------------

class TestInlineRules:
    """Rules prefixed with ``_`` are marked ``inline=True`` in the BnfSpec."""

    def _rule(self, spec: BnfSpec, name: str) -> RuleSpec:
        return next(r for r in spec.rules if r.lhs == name)

    _TEXT = (
        ":GRAMMAR\n"
        "start ::= a ;\n"
        "_ a ::= A ;\n"
        ":TERMINALS\n"
        "A /a/ ;\n"
    )

    def test_inline_flag_set(self):
        spec = parse_bnf(self._TEXT)
        assert self._rule(spec, "a").inline == InlineType.INLINE

    def test_non_inline_flag_not_set(self):
        spec = parse_bnf(self._TEXT)
        assert self._rule(spec, "start").inline == InlineType.NONE

    def test_lhs_is_rule_name_not_underscore(self):
        spec = parse_bnf(self._TEXT)
        lhs_names = [r.lhs for r in spec.rules]
        assert "a" in lhs_names
        assert "_" not in lhs_names

    def test_inline_rule_alternatives(self):
        spec = parse_bnf(self._TEXT)
        rule = self._rule(spec, "a")
        assert rule.alternatives == (Rhs(("A",)),)

    def test_inline_rule_multi_alternative(self):
        text = (
            ":GRAMMAR\n"
            "start ::= item ;\n"
            "_ item ::= A | B ;\n"
            ":TERMINALS\n"
            "A /a/ ;\n"
            "B /b/ ;\n"
        )
        spec = parse_bnf(text)
        rule = self._rule(spec, "item")
        assert rule.inline == InlineType.INLINE
        syms = {alt.symbols for alt in rule.alternatives}
        assert ("A",) in syms
        assert ("B",) in syms
