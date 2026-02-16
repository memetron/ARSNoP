"""Tests for Automaton.trace()."""

from arsnop.grammar import Grammar
from arsnop.lexer import Lexer, Token
from arsnop.parser.shift_reduce import LR1, ShiftReduceTrace, TraceStep, TraceAction


GRAMMAR_TEXT = "start ::= expr\nexpr ::= expr PLUS term | term\nterm ::= NUM"
TERMINALS_TEXT = "PLUS \\+\nNUM [0-9]+\nSPC [ ]\n.IGNORE\nSPC"


def _build_automaton(grammar_text=GRAMMAR_TEXT):
    grammar = Grammar(grammar_text)
    return LR1().generate(grammar)


def _lex(input_text, terminals_text=TERMINALS_TEXT):
    return Lexer(terminals_text).lex(input_text)


class TestTraceReturnType:
    def test_returns_shift_reduce_trace(self):
        automaton = _build_automaton()
        tokens = _lex("1 + 2")
        result = automaton.trace(tokens)
        assert isinstance(result, ShiftReduceTrace)

    def test_steps_are_trace_steps(self):
        automaton = _build_automaton()
        tokens = _lex("1")
        result = automaton.trace(tokens)
        assert all(isinstance(s, TraceStep) for s in result.steps)

    def test_actions_are_trace_actions(self):
        automaton = _build_automaton()
        tokens = _lex("1")
        result = automaton.trace(tokens)
        assert all(isinstance(s.action, TraceAction) for s in result.steps)


class TestTraceSteps:
    def test_has_shift_reduce_accept(self):
        automaton = _build_automaton()
        tokens = _lex("1 + 2")
        result = automaton.trace(tokens)
        action_types = {s.action.type for s in result.steps}
        assert "shift" in action_types
        assert "reduce" in action_types
        assert "accept" in action_types

    def test_last_step_is_accept(self):
        automaton = _build_automaton()
        tokens = _lex("1")
        result = automaton.trace(tokens)
        assert result.steps[-1].action.type == "accept"

    def test_step_numbers_sequential(self):
        automaton = _build_automaton()
        tokens = _lex("1 + 2")
        result = automaton.trace(tokens)
        for i, step in enumerate(result.steps):
            assert step.step == i

    def test_stack_is_tuple(self):
        automaton = _build_automaton()
        tokens = _lex("1")
        result = automaton.trace(tokens)
        assert all(isinstance(s.stack, tuple) for s in result.steps)

    def test_input_buffer_is_tuple(self):
        automaton = _build_automaton()
        tokens = _lex("1")
        result = automaton.trace(tokens)
        assert all(isinstance(s.input_buffer, tuple) for s in result.steps)

    def test_shift_action_has_state(self):
        automaton = _build_automaton()
        tokens = _lex("1")
        result = automaton.trace(tokens)
        shift_steps = [s for s in result.steps if s.action.type == "shift"]
        assert len(shift_steps) > 0
        for s in shift_steps:
            assert s.action.state is not None

    def test_reduce_action_has_production(self):
        automaton = _build_automaton()
        tokens = _lex("1")
        result = automaton.trace(tokens)
        reduce_steps = [s for s in result.steps if s.action.type == "reduce"]
        assert len(reduce_steps) > 0
        for s in reduce_steps:
            assert s.action.production is not None


class TestTraceASTConsistency:
    def test_ast_matches_parse(self):
        automaton = _build_automaton()
        tokens = _lex("1 + 2")
        trace_result = automaton.trace(tokens)
        parse_result = automaton.parse(tokens)
        assert trace_result.ast is not None
        assert str(trace_result.ast) == str(parse_result)

    def test_no_error_on_success(self):
        automaton = _build_automaton()
        tokens = _lex("1")
        result = automaton.trace(tokens)
        assert result.error is None

    def test_tokens_preserved(self):
        automaton = _build_automaton()
        tokens = _lex("1 + 2")
        result = automaton.trace(tokens)
        assert len(result.tokens) == len(tokens)


class TestTraceError:
    def test_error_on_unexpected_token(self):
        automaton = _build_automaton()
        tokens = [Token("PLUS", "+")]
        result = automaton.trace(tokens)
        assert result.ast is None
        assert result.error is not None
        assert "Unexpected token" in result.error

    def test_error_has_partial_trace(self):
        automaton = _build_automaton()
        tokens = [Token("NUM", "1"), Token("NUM", "2")]
        result = automaton.trace(tokens)
        assert result.ast is None
        assert result.error is not None
        assert len(result.steps) > 0
