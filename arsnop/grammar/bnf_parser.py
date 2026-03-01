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
from .bnf_types import Rhs, BnfSpec, RuleSpec, TerminalSpec

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
    TerminalSpec("ID",           r'[a-zA-Z]\w*'),
    TerminalSpec("MODIFIER",    r"\*|\+|\?"),
    TerminalSpec("OPEN_PAREN",    r"\("),
    TerminalSpec("CLOSE_PAREN",   r"\)"),
    TerminalSpec("INLINE", r"_"),
    TerminalSpec("CONDITIONAL_INLINE", r"_\?"),
    TerminalSpec("LABEL_MARKER", r":"),
], ignored=["WS"])

_GRAMMAR = Grammar([
    RuleSpec("bnf_file", (
        Rhs(("GRAMMAR_KW", "rules_section", "TERMINALS_KW", "terminals_section")),
    )),
    RuleSpec("rules_section", (
        Rhs(("rules_section", "rule")),
        Rhs(()),
    )),
    RuleSpec("optional_inline", (
        Rhs(("INLINE",)),
        Rhs(("CONDITIONAL_INLINE",)),
        Rhs(()),
    )),
    RuleSpec("rule", (
        Rhs(("optional_inline", "ID", "ARROW", "alternatives", "SEMI")),
    )),
    RuleSpec("alternatives", (
        Rhs(("alternatives", "PIPE", "alternative", "optional_label")),
        Rhs(("alternative", "optional_label")),
    )),
    RuleSpec("optional_label", (
        Rhs(("LABEL_MARKER", "ID")),
        Rhs(()),
    )),
    RuleSpec("alternative", (
        Rhs(("alternative", "atom", "MODIFIER")),
        Rhs(("alternative", "atom", "CONDITIONAL_INLINE")),
        Rhs(("alternative", "atom")),
        Rhs(()),
    )),
    RuleSpec("atom", (
        Rhs(("ID",)),
        Rhs(("QUOTED",)),
        Rhs(("REGEX",)),
        Rhs(("OPEN_PAREN", "alternatives", "CLOSE_PAREN")),
    )),
    RuleSpec("terminals_section", (
        Rhs(("terminals_section", "terminal_def")),
        Rhs(("terminals_section", "ignore_section")),
        Rhs(()),
    )),
    RuleSpec("terminal_def", (
        Rhs(("ID", "REGEX", "SEMI")),
        Rhs(("ID", "QUOTED", "SEMI")),
    )),
    RuleSpec("ignore_section", (
        Rhs(("IGNORE_KW", "ignore_names", "SEMI")),
    )),
    RuleSpec("ignore_names", (
        Rhs(("ignore_names", "ID")),
        Rhs(("ID",)),
    )),
], start_symbol="bnf_file")

def parse_bnf_ast(text: str) -> AST:
    """Parse a complete BNF file text and return the raw ``AST``."""
    return Earley(_GRAMMAR).parse(_LEXER.lex(text))

def parse_bnf(text: str) -> BnfSpec:
    """Parse a complete BNF file text and return a ``BnfSpec``."""
    return cast(BnfSpec, BnfSpecTransformer().transform(parse_bnf_ast(text)))
