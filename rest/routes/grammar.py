from flask import Blueprint, jsonify, request

from arsnop.grammar import Grammar, parse_bnf
from ..grammar_store import list_bundled, load_bundled
from ..serializers import serialize_production

grammar_bp = Blueprint("grammar", __name__, url_prefix="/api/grammar")


@grammar_bp.route("/bundled", methods=["GET"])
def get_bundled_list():
    return jsonify(list_bundled())


@grammar_bp.route("/bundled/<name>", methods=["GET"])
def get_bundled_text(name):
    try:
        text = load_bundled(name)
        return jsonify({"name": name, "text": text})
    except FileNotFoundError as e:
        return jsonify({"error": "not_found", "message": str(e)}), 404


@grammar_bp.route("/analyze", methods=["POST"])
def analyze_grammar():
    data = request.get_json(force=True)
    grammar_text = data.get("grammar", "")

    try:
        spec = parse_bnf(grammar_text)
    except ValueError:
        return jsonify({
            "error": "invalid_format",
            "message": "Grammar must contain :GRAMMAR and :TERMINALS sections",
        }), 400

    try:
        grammar = Grammar(spec.rules)
    except Exception as e:
        return jsonify({"error": "grammar_error", "message": str(e)}), 400

    first_sets = {}
    follow_sets = {}
    for nt in sorted(grammar.non_terminals):
        first_sets[nt] = sorted(grammar.first(nt))
        follow_sets[nt] = sorted(grammar.follow(nt))

    return jsonify({
        "terminals": sorted(grammar.terminals),
        "nonTerminals": sorted(grammar.non_terminals),
        "productions": [serialize_production(p) for p in grammar.productions],
        "firstSets": first_sets,
        "followSets": follow_sets,
    })
