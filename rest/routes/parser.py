from flask import Blueprint, jsonify, request

from arsnop.grammar import Grammar
from arsnop.lexer import Lexer
from arsnop.parser import parse_grammar_text
from arsnop.parser.earley import Earley
from arsnop.parser.shift_reduce import LR0, SLR, LR1, LALR, LALR_Brute_Force
from arsnop.parser.shift_reduce.automaton import Automaton
from ..serializers import (
    serialize_state,
    serialize_action_table,
    serialize_goto_table,
    serialize_shift_reduce_trace,
    serialize_earley_trace,
)

parser_bp = Blueprint("parser", __name__, url_prefix="/api/parse")

_GENERATORS = {
    "lr0": LR0,
    "slr": SLR,
    "lr1": LR1,
    "lalr": LALR,
    "lalr_brute_force": LALR_Brute_Force,
}


def _load_grammar(grammar_text):
    """Parse grammar text and return (Grammar, terminals_section) or raise."""
    grammar_section, terminals_section = parse_grammar_text(grammar_text)
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
        grammar, _ = _load_grammar(grammar_text)
    except ValueError as e:
        return jsonify({"error": "invalid_format", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "grammar_error", "message": str(e)}), 400

    try:
        result = _GENERATORS[variant]().generate_tables(grammar)
    except Exception as e:
        return jsonify({"error": "table_error", "message": str(e)}), 400

    return jsonify({
        "states": [serialize_state(i, s) for i, s in enumerate(result.states)],
        "actionTable": serialize_action_table(result.action_table),
        "gotoTable": serialize_goto_table(result.goto_table),
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
        grammar, terminals_section = _load_grammar(grammar_text)
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
            trace = Earley.trace(grammar, tokens)
        except Exception as e:
            return jsonify({"error": "parse_error", "message": str(e)}), 400
        return jsonify(serialize_earley_trace(trace))

    try:
        result = _GENERATORS[variant]().generate_tables(grammar)
    except Exception as e:
        return jsonify({"error": "table_error", "message": str(e)}), 400

    automaton = Automaton(result.goto_table, result.action_table)
    trace = automaton.trace(tokens)
    return jsonify(serialize_shift_reduce_trace(trace))
