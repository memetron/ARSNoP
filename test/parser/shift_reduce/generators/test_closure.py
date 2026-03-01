"""Tests for the shared closure primitives."""
from arsnop.grammar import Grammar, Production
from arsnop.grammar.bnf_parser import parse_bnf
from arsnop.parser.shift_reduce.state import Item
from arsnop.parser.shift_reduce.generators.closure import (
    augmented_start,
    build_states,
    closure_step,
    lr0_closure,
    lr1_closure,
    lr1_lookahead,
    successor,
)

from .conftest import SIMPLE_BNF, NULLABLE_BNF

GRAMMAR = Grammar(parse_bnf(SIMPLE_BNF).rules)   # start ::= expr; expr ::= TOK
NULLABLE = Grammar(parse_bnf(NULLABLE_BNF).rules) # start ::= A B c; A ::= a | ε; B ::= b | ε


class TestAugmentedStart:
    def test_lhs_is_s_prime(self):
        prod = augmented_start(GRAMMAR)
        assert prod.lhs == "S'"

    def test_rhs_is_start_symbol(self):
        prod = augmented_start(GRAMMAR)
        assert prod.rhs == (GRAMMAR.start_symbol,)


class TestClosureStep:
    def test_expands_non_terminal(self):
        """closure_step should add productions for the symbol after the dot."""
        start = Production("S'", ("start",))
        initial = frozenset([Item(start, 0)])
        result = closure_step(initial, GRAMMAR, lambda _i, _g: frozenset())
        prods = {item.production.lhs for item in result}
        assert "start" in prods
        assert "expr" in prods

    def test_no_expansion_for_terminal(self):
        """Items whose dot is before a terminal should not expand."""
        tok_prod = Production("expr", ("TOK",))
        initial = frozenset([Item(tok_prod, 0)])
        result = closure_step(initial, GRAMMAR, lambda _i, _g: frozenset())
        assert result == initial

    def test_complete_item_unchanged(self):
        """An item with the dot at the end should not cause expansion."""
        prod = Production("expr", ("TOK",))
        complete = Item(prod, 1)
        initial = frozenset([complete])
        result = closure_step(initial, GRAMMAR, lambda _i, _g: frozenset())
        assert result == initial


class TestLr0Closure:
    def test_items_have_empty_lookahead(self):
        start = augmented_start(GRAMMAR)
        items = lr0_closure(GRAMMAR, [Item(start, 0)])
        for item in items:
            assert item.lookahead == frozenset()

    def test_expands_start(self):
        start = augmented_start(GRAMMAR)
        items = lr0_closure(GRAMMAR, [Item(start, 0)])
        lhs_set = {item.production.lhs for item in items}
        assert lhs_set == {"S'", "start", "expr"}


class TestLr1Lookahead:
    def test_lookahead_from_following_terminal(self):
        """Remainder symbols contribute their FIRST sets to the lookahead."""
        # start ::= A B c; at dot=0 remainder is [B, c]
        # FIRST(B) = {b, ε} → b added, B nullable so continue
        # FIRST(c) = {c} → c added, not nullable so stop
        prod = Production("start", ("A", "B", "c"))
        item = Item(prod, 0, frozenset({"$"}))
        la = lr1_lookahead(item, NULLABLE)
        assert la == frozenset({"b", "c"})

    def test_lookahead_falls_through_to_item_lookahead(self):
        """When the entire remainder is nullable, the item's own lookahead propagates."""
        # start ::= A B c, with dot=0, remainder=[B, c]
        # But let's use a production where remainder is empty
        prod = Production("expr", ("TOK",))
        item = Item(prod, 0, frozenset({"$"}))
        la = lr1_lookahead(item, GRAMMAR)
        # remainder is empty → falls through to item.lookahead
        assert la == frozenset({"$"})

    def test_no_epsilon_in_result(self):
        """lr1_lookahead should never return epsilon."""
        prod = Production("start", ("A", "B", "c"))
        item = Item(prod, 0, frozenset({"$"}))
        la = lr1_lookahead(item, NULLABLE)
        assert "" not in la


class TestLr1Closure:
    def test_propagates_lookahead(self):
        start = augmented_start(GRAMMAR)
        items = lr1_closure(GRAMMAR, [Item(start, 0, frozenset({"$"}))])
        for item in items:
            assert len(item.lookahead) > 0

    def test_no_epsilon_in_lookahead(self):
        start = augmented_start(NULLABLE)
        items = lr1_closure(NULLABLE, [Item(start, 0, frozenset({"$"}))])
        for item in items:
            assert "" not in item.lookahead


class TestSuccessor:
    def test_advances_matching_items(self):
        prod = Production("expr", ("TOK",))
        items = [Item(prod, 0)]
        result = successor(GRAMMAR, items, "TOK", lr0_closure)
        dots = {item.dot for item in result if item.production == prod}
        assert 1 in dots

    def test_returns_empty_for_non_matching_symbol(self):
        prod = Production("expr", ("TOK",))
        items = [Item(prod, 0)]
        result = successor(GRAMMAR, items, "NOMATCH", lr0_closure)
        assert result == frozenset()

    def test_preserves_lookahead(self):
        prod = Production("expr", ("TOK",))
        la = frozenset({"$"})
        items = [Item(prod, 0, la)]
        result = successor(GRAMMAR, items, "TOK", lr1_closure)
        for item in result:
            if item.production == prod:
                assert item.lookahead == la


class TestBuildStates:
    def test_lr0_produces_states_and_transitions(self):
        start = [Item(augmented_start(GRAMMAR), 0)]
        states, transitions = build_states(GRAMMAR, start, lr0_closure)
        assert len(states) > 1
        assert len(transitions) > 0

    def test_lr1_produces_states_and_transitions(self):
        start = [Item(augmented_start(GRAMMAR), 0, frozenset({"$"}))]
        states, transitions = build_states(GRAMMAR, start, lr1_closure)
        assert len(states) > 1
        assert len(transitions) > 0

    def test_start_state_is_first(self):
        start_items = [Item(augmented_start(GRAMMAR), 0)]
        states, _ = build_states(GRAMMAR, start_items, lr0_closure)
        start_prods = {
            item.production for item in states[0].items if item.production.lhs == "S'"
        }
        assert len(start_prods) == 1

    def test_transitions_reference_valid_states(self):
        start = [Item(augmented_start(GRAMMAR), 0)]
        states, transitions = build_states(GRAMMAR, start, lr0_closure)
        for (src, _), tgt in transitions.items():
            assert 0 <= src < len(states)
            assert 0 <= tgt < len(states)

    def test_no_duplicate_states(self):
        start = [Item(augmented_start(GRAMMAR), 0)]
        states, _ = build_states(GRAMMAR, start, lr0_closure)
        assert len(states) == len(set(states))
