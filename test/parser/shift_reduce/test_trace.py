"""Tests for Automaton.trace()."""

from arsnop.grammar import Grammar
from arsnop.grammar.bnf_parser import parse_bnf
from arsnop.lexer import Lexer
from arsnop.parser.shift_reduce import LR1, ShiftReduceTrace, TraceStep, TraceAction


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


def _build_automaton(bnf_text: str = BNF_TEXT):
    grammar = Grammar(parse_bnf(bnf_text).rules)
    return LR1().generate(grammar)


class TestTraceReturnType:
    def test_returns_shift_reduce_trace(self):
        automaton = _build_automaton()
        result = automaton.trace("1 + 2", _LEXER)
        assert isinstance(result, ShiftReduceTrace)

    def test_steps_are_trace_steps(self):
        automaton = _build_automaton()
        result = automaton.trace("1", _LEXER)
        assert all(isinstance(s, TraceStep) for s in result.steps)

    def test_actions_are_trace_actions(self):
        automaton = _build_automaton()
        result = automaton.trace("1", _LEXER)
        assert all(isinstance(s.action, TraceAction) for s in result.steps)


class TestTraceSteps:
    def test_has_shift_reduce_accept(self):
        automaton = _build_automaton()
        result = automaton.trace("1 + 2", _LEXER)
        action_types = {s.action.type for s in result.steps}
        assert "shift" in action_types
        assert "reduce" in action_types
        assert "accept" in action_types

    def test_last_step_is_accept(self):
        automaton = _build_automaton()
        result = automaton.trace("1", _LEXER)
        assert result.steps[-1].action.type == "accept"

    def test_step_numbers_sequential(self):
        automaton = _build_automaton()
        result = automaton.trace("1 + 2", _LEXER)
        for i, step in enumerate(result.steps):
            assert step.step == i

    def test_stack_is_tuple(self):
        automaton = _build_automaton()
        result = automaton.trace("1", _LEXER)
        assert all(isinstance(s.stack, tuple) for s in result.steps)

    def test_input_buffer_is_tuple(self):
        automaton = _build_automaton()
        result = automaton.trace("1", _LEXER)
        assert all(isinstance(s.input_buffer, tuple) for s in result.steps)

    def test_shift_action_has_state(self):
        automaton = _build_automaton()
        result = automaton.trace("1", _LEXER)
        shift_steps = [s for s in result.steps if s.action.type == "shift"]
        assert len(shift_steps) > 0
        for s in shift_steps:
            assert s.action.state is not None

    def test_reduce_action_has_production(self):
        automaton = _build_automaton()
        result = automaton.trace("1", _LEXER)
        reduce_steps = [s for s in result.steps if s.action.type == "reduce"]
        assert len(reduce_steps) > 0
        for s in reduce_steps:
            assert s.action.production is not None


class TestTraceASTConsistency:
    def test_ast_matches_parse(self):
        automaton = _build_automaton()
        trace_result = automaton.trace("1 + 2", _LEXER)
        parse_result = automaton.parse("1 + 2", _LEXER)
        assert trace_result.ast is not None
        assert str(trace_result.ast) == str(parse_result)

    def test_no_error_on_success(self):
        automaton = _build_automaton()
        result = automaton.trace("1", _LEXER)
        assert result.error is None

    def test_tokens_preserved(self):
        automaton = _build_automaton()
        result = automaton.trace("1 + 2", _LEXER)
        # "1 + 2" → 3 tokens (NUM, PLUS, NUM)
        assert len(result.tokens) == 3


_EBNF_BNF_TEXT = (
    ":GRAMMAR\n"
    "start ::= a* ;\n"
    "a ::= A ;\n"
    ":TERMINALS\n"
    "A /A/ ;\n"
)

_EBNF_SPEC = parse_bnf(_EBNF_BNF_TEXT)
_EBNF_LEXER = Lexer(_EBNF_SPEC.terminals, _EBNF_SPEC.ignored)


def _build_ebnf_automaton():
    return LR1().generate(Grammar(_EBNF_SPEC.rules))


class TestModifierInlining:
    """EBNF-generated aux rule nodes should be absent from the AST entirely."""

    def _ast(self, input_text: str):
        return _build_ebnf_automaton().parse(input_text, _EBNF_LEXER)

    def test_star_empty_start_has_no_children(self):
        ast = self._ast("")
        assert ast.content == "start"
        assert ast.children == []

    def test_star_single_child_directly_on_start(self):
        ast = self._ast("A")
        assert ast.content == "start"
        assert len(ast.children) == 1
        assert ast.children[0].content == "a"

    def test_star_multiple_children_directly_on_start(self):
        ast = self._ast("AAA")
        assert ast.content == "start"
        assert len(ast.children) == 3

    def test_star_no_aux_node_in_tree(self):
        ast = self._ast("AAA")
        assert all(child.content != "_a_star" for child in ast.children)

    def test_star_children_are_a_nodes(self):
        ast = self._ast("AAA")
        assert all(child.content == "a" for child in ast.children)


class TestTraceError:
    def test_error_on_unexpected_token(self):
        automaton = _build_automaton()
        # "+" cannot be lexed in the initial state (only NUM is expected)
        result = automaton.trace("+", _LEXER)
        assert result.ast is None
        assert result.error is not None

    def test_error_has_partial_trace(self):
        automaton = _build_automaton()
        # "1 2": after shifting NUM, only PLUS is a valid next terminal
        # so "2" cannot be lexed → lex error, but at least 1 step recorded
        result = automaton.trace("1 2", _LEXER)
        assert result.ast is None
        assert result.error is not None
        assert len(result.steps) > 0
