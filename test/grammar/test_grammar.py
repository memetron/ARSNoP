"""Tests for src/grammar/grammar.py."""
from arsnop.grammar import Grammar


SIMPLE_GRAMMAR = "start ::= expr\nexpr ::= TOK"

ARITH_GRAMMAR = "start ::= expr\nexpr ::= expr OP NUM | NUM"

# Grammar with nullable rules: A and B can derive epsilon
NULLABLE_GRAMMAR = "start ::= A B c\nA ::= a | \nB ::= b | "

MULTI_PRODUCTION = (
    "start ::= list\n"
    "list ::= LP items RP\n"
    "items ::= ITEM SEP items | ITEM"
)


class TestGrammarParsing:
    def test_terminals_and_nonterminals(self):
        g = Grammar(SIMPLE_GRAMMAR)
        assert "TOK" in g.terminals
        assert "start" in g.non_terminals
        assert "expr" in g.non_terminals
        # terminals should not include non-terminals
        assert "start" not in g.terminals
        assert "expr" not in g.terminals

    def test_productions_count(self):
        g = Grammar(SIMPLE_GRAMMAR)
        assert len(g.productions) == 2

    def test_start_symbol_default(self):
        g = Grammar(SIMPLE_GRAMMAR)
        assert g.start_symbol == "start"

    def test_start_symbol_custom(self):
        g = Grammar("root ::= TOK", start_symbol="root")
        assert g.start_symbol == "root"

    def test_multiple_alternatives(self):
        g = Grammar(ARITH_GRAMMAR)
        expr_prods = [p for p in g.productions if p.lhs == "expr"]
        assert len(expr_prods) == 2

    def test_multi_rule_grammar(self):
        g = Grammar(MULTI_PRODUCTION)
        assert "list" in g.non_terminals
        assert "items" in g.non_terminals
        assert "LP" in g.terminals
        assert "RP" in g.terminals
        assert "SEP" in g.terminals
        assert "ITEM" in g.terminals


class TestLookupProductions:
    def test_lookup_existing(self):
        g = Grammar(SIMPLE_GRAMMAR)
        prods = g.lookup_productions("start")
        assert len(prods) == 1
        assert prods[0].lhs == "start"
        assert prods[0].rhs == ("expr",)

    def test_lookup_multiple(self):
        g = Grammar(ARITH_GRAMMAR)
        prods = g.lookup_productions("expr")
        assert len(prods) == 2

    def test_lookup_nonexistent(self):
        g = Grammar(SIMPLE_GRAMMAR)
        prods = g.lookup_productions("nonexistent")
        assert prods == []


class TestIsNullable:
    def test_nullable_false_for_non_nullable(self):
        g = Grammar(SIMPLE_GRAMMAR)
        assert g.is_nullable("start") is False
        assert g.is_nullable("expr") is False


class TestFirstSets:
    def test_first_of_terminal(self):
        g = Grammar(SIMPLE_GRAMMAR)
        assert g.first("TOK") == {"TOK"}

    def test_first_of_nonterminal(self):
        g = Grammar(SIMPLE_GRAMMAR)
        first_start = g.first("start")
        assert "TOK" in first_start

    def test_first_with_alternatives(self):
        g = Grammar(ARITH_GRAMMAR)
        first_expr = g.first("expr")
        assert "NUM" in first_expr

    def test_first_with_nullable(self):
        g = Grammar(NULLABLE_GRAMMAR)
        first_start = g.first("start")
        # start ::= A B c; A is nullable so first(start) should include first(B)
        # B is also nullable so first(start) should include first(c) = {c}
        assert "a" in first_start
        assert "b" in first_start
        assert "c" in first_start

    def test_first_nullable_nonterminal_contains_epsilon(self):
        g = Grammar(NULLABLE_GRAMMAR)
        first_a = g.first("A")
        assert "a" in first_a
        assert "" in first_a  # A can derive epsilon


class TestFollowSets:
    def test_follow_start_contains_dollar(self):
        g = Grammar(SIMPLE_GRAMMAR)
        assert "$" in g.follow("start")

    def test_follow_nonterminal(self):
        g = Grammar(SIMPLE_GRAMMAR)
        follow_expr = g.follow("expr")
        # expr is the only production of start, so follow(expr) should include $
        assert "$" in follow_expr

    def test_follow_with_successor(self):
        g = Grammar(NULLABLE_GRAMMAR)
        follow_a = g.follow("A")
        # start ::= A B c; after A comes B, so first(B) - {eps} should be in follow(A)
        assert "b" in follow_a
        # B is nullable, so first(c) = {c} should also be in follow(A)
        assert "c" in follow_a

    def test_follow_with_nullable_successor(self):
        g = Grammar(NULLABLE_GRAMMAR)
        follow_b = g.follow("B")
        # start ::= A B c; after B comes c, so first(c) = {c} should be in follow(B)
        assert "c" in follow_b
