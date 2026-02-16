import re

from flask import Blueprint, jsonify, request

from arsnop.grammar import Grammar
from arsnop.lexer import Lexer
from arsnop.parser.parser import _GRAMMAR_FORMAT
from arsnop.parser.shift_reduce import LR0, SLR, LR1, LALR, LALR_Brute_Force
from arsnop.parser.shift_reduce.generators.generator import (
    _build_action_table,
    _build_goto_table,
)
from ..serializers import (
    serialize_state,
    serialize_action_table,
    serialize_goto_table,
)
from ..tracer import traced_parse
from ..earley_tracer import traced_earley_parse

parser_bp = Blueprint("parser", __name__, url_prefix="/api/parse")

_GENERATORS = {
    "lr0": LR0,
    "slr": SLR,
    "lr1": LR1,
    "lalr": LALR,
    "lalr_brute_force": LALR_Brute_Force,
}


def _parse_grammar_text(grammar_text):
    """Parse grammar text and return (Grammar, terminals_section) or raise ValueError."""
    match = re.match(_GRAMMAR_FORMAT, grammar_text)
    if not match:
        raise ValueError("Grammar must contain :GRAMMAR and :TERMINALS sections")
    grammar_section, terminals_section = match.groups()
    return Grammar(grammar_section), terminals_section


@parser_bp.route("/tables", methods=["POST"])
def generate_tables():
    data = request.get_json(force=True)
    grammar_text = data.get("grammar", "")
    variant = data.get("variant", "lr0")

    if variant == "earley":
        return jsonify({
            "error": "invalid_variant",
            "message": "Earley parser does not use precomputed tables. Use the parse endpoint instead.",
        }), 400

    if variant not in _GENERATORS:
        return jsonify({
            "error": "invalid_variant",
            "message": f"Unknown parser variant '{variant}'. Options: {list(_GENERATORS.keys())}",
        }), 400

    try:
        grammar, _ = _parse_grammar_text(grammar_text)
    except ValueError as e:
        return jsonify({"error": "invalid_format", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "grammar_error", "message": str(e)}), 400

    try:
        gen = _GENERATORS[variant]()
        states, transitions = gen._build_states(grammar)
        action = _build_action_table(
            grammar, states, transitions, gen._reduce_lookaheads,
        )
        goto = _build_goto_table(grammar, transitions)
    except Exception as e:
        return jsonify({"error": "table_error", "message": str(e)}), 400

    return jsonify({
        "states": [serialize_state(i, s) for i, s in enumerate(states)],
        "actionTable": serialize_action_table(action),
        "gotoTable": serialize_goto_table(goto),
    })


@parser_bp.route("/execute", methods=["POST"])
def execute_parse():
    data = request.get_json(force=True)
    grammar_text = data.get("grammar", "")
    variant = data.get("variant", "lr0")
    input_text = data.get("input", "")

    all_variants = ["earley"] + list(_GENERATORS.keys())
    if variant not in all_variants:
        return jsonify({
            "error": "invalid_variant",
            "message": f"Unknown parser variant '{variant}'. Options: {all_variants}",
        }), 400

    try:
        grammar, terminals_section = _parse_grammar_text(grammar_text)
    except ValueError as e:
        return jsonify({"error": "invalid_format", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "grammar_error", "message": str(e)}), 400

    try:
        lexer = Lexer(terminals_section)
    except Exception as e:
        return jsonify({"error": "lexer_error", "message": str(e)}), 400

    try:
        tokens = lexer.lex(input_text)
    except Exception as e:
        return jsonify({"error": "lex_error", "message": str(e)}), 400

    if variant == "earley":
        try:
            result = traced_earley_parse(grammar, tokens)
        except Exception as e:
            return jsonify({"error": "parse_error", "message": str(e)}), 400
        return jsonify(result)

    try:
        gen = _GENERATORS[variant]()
        states, transitions = gen._build_states(grammar)
        action = _build_action_table(
            grammar, states, transitions, gen._reduce_lookaheads,
        )
        goto = _build_goto_table(grammar, transitions)
    except Exception as e:
        return jsonify({"error": "table_error", "message": str(e)}), 400

    result = traced_parse(action, goto, tokens)
    return jsonify(result)
