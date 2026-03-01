"""BNF parser using an Earley parser for the semicolon-terminated BNF format.

Rules and terminal definitions are terminated with ``;``.  Newlines are
whitespace — ignored by the lexer — so multi-line rules require no special
handling.

Public API: parse_bnf, parse_bnf_ast, BnfSpecTransformer.
"""
from __future__ import annotations

from typing import cast

from ..lexer import Lexer
from ..ast import AST
from ..parser.earley.earley import Earley
from .grammar import Grammar
from .bnf_transformer import BnfSpecTransformer
from .bnf_types import Alternative, BnfSpec, RuleSpec, TerminalSpec

_LEXER = Lexer([
    TerminalSpec("GRAMMAR_KW",   r":GRAMMAR"),
    TerminalSpec("TERMINALS_KW", r":TERMINALS"),
    TerminalSpec("IGNORE_KW",    r"\.IGNORE"),
    TerminalSpec("ARROW",        r"::="),
    TerminalSpec("PIPE",         r"\|"),
    TerminalSpec("SEMI",         r";"),
    TerminalSpec("QUOTED",       r'"(?:[^"\\]|\\.)*"'),
    TerminalSpec("REGEX",        r'/(?:[^/\\]|\\.)*/' ),
    TerminalSpec("WS",           r"[ \t\n\r]+"),
    TerminalSpec("WORD",         r'[a-zA-Z_]\w*'),
], ignored=["WS"])

_GRAMMAR = Grammar([
    RuleSpec("bnf_file", (
        Alternative(("GRAMMAR_KW", "rules_section", "TERMINALS_KW", "terminals_section")),
    )),
    RuleSpec("rules_section", (
        Alternative(("rules_section", "rule")),
        Alternative(()),
    )),
    RuleSpec("rule", (
        Alternative(("WORD", "ARROW", "alternatives", "SEMI")),
    )),
    RuleSpec("alternatives", (
        Alternative(("alternatives", "PIPE", "alternative")),
        Alternative(("alternative",)),
    )),
    RuleSpec("alternative", (
        Alternative(("alternative", "WORD")),
        Alternative(()),
    )),
    RuleSpec("terminals_section", (
        Alternative(("terminals_section", "terminal_def")),
        Alternative(("terminals_section", "ignore_section")),
        Alternative(()),
    )),
    RuleSpec("terminal_def", (
        Alternative(("WORD", "REGEX", "SEMI")),
        Alternative(("WORD", "QUOTED", "SEMI")),
    )),
    RuleSpec("ignore_section", (
        Alternative(("IGNORE_KW", "ignore_names", "SEMI")),
    )),
    RuleSpec("ignore_names", (
        Alternative(("ignore_names", "WORD")),
        Alternative(("WORD",)),
    )),
], start_symbol="bnf_file")

def parse_bnf_ast(text: str) -> AST:
    """Parse a complete BNF file text and return the raw ``AST``."""
    return Earley(_GRAMMAR).parse(_LEXER.lex(text))

def parse_bnf(text: str) -> BnfSpec:
    """Parse a complete BNF file text and return a ``BnfSpec``."""
    return cast(BnfSpec, BnfSpecTransformer().transform(parse_bnf_ast(text)))
