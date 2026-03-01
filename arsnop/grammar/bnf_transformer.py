"""Transformer that converts a BNF parse tree into typed ``BnfSpec`` objects.

The BNF grammar is left-recursive, so the Earley AST uses left-associative
trees for all list-like constructs.  Each visitor method receives the already-
transformed children and incrementally builds the result.
"""
from __future__ import annotations

import re
from typing import Any

from ..transformer import Transformer
from .bnf_types import Alternative, BnfSpec, RuleSpec, TerminalSpec


class BnfSpecTransformer(Transformer):
    """Transforms a BNF parse tree into ``BnfSpec`` (and its component types).

    Subclass this to handle EBNF extensions or other grammar variants.
    Override individual visit methods — the base ``Transformer`` dispatches
    by node name via ``getattr``.
    """

    def bnf_file(self, children: list[Any]) -> BnfSpec:
        """Combine rules and terminals sections into a ``BnfSpec``.

        children: [":GRAMMAR", rules_list, ":TERMINALS", (terminals, ignored)]
        """
        rules: list[RuleSpec] = children[1]
        terminals: list[TerminalSpec]
        ignored: list[str]
        terminals, ignored = children[3]
        return BnfSpec(
            rules=tuple(rules),
            terminals=tuple(terminals),
            ignored=tuple(ignored),
        )

    def rules_section(self, children: list[Any]) -> list[RuleSpec]:
        """Incrementally build the rules list from left-recursive children.

        children: [] for empty base case, or [prev_list, rule] for recursive.
        """
        if not children:
            return []
        return children[0] + [children[1]]

    def rule(self, children: list[Any]) -> RuleSpec:
        """Build a ``RuleSpec`` from its lhs name and alternatives list.

        children: [lhs_str, "::=", alts_list, ";"]
        """
        lhs: str = children[0]
        alternatives: list[Alternative] = children[2]
        return RuleSpec(lhs=lhs, alternatives=tuple(alternatives))

    def alternatives(self, children: list[Any]) -> list[Alternative]:
        """Incrementally build the alternatives list from left-recursive children.

        children: [alt] for base case, or [alts_list, "|", alt] for recursive.
        """
        if len(children) == 1:
            return [children[0]]
        return children[0] + [children[2]]

    def alternative(self, children: list[Any]) -> Alternative:
        """Build an ``Alternative`` incrementally from left-recursive children.

        children: [] for empty base case, or [prev_alt, word_str] for recursive.
        """
        if not children:
            return Alternative(symbols=())
        prev: Alternative = children[0]
        word: str = children[1]
        return Alternative(symbols=prev.symbols + (word,))

    def terminals_section(
        self, children: list[Any]
    ) -> tuple[list[TerminalSpec], list[str]]:
        """Incrementally build the terminals and ignored lists.

        children: [] for empty base case, or [prev_result, item] for recursive.
        item is a TerminalSpec or a list[str] from ignore_section.
        """
        if not children:
            return [], []
        prev_terms: list[TerminalSpec]
        prev_ignored: list[str]
        prev_terms, prev_ignored = children[0]
        item = children[1]
        if isinstance(item, TerminalSpec):
            return prev_terms + [item], prev_ignored
        return prev_terms, prev_ignored + item  # item is list[str] from ignore_section

    def terminal_def(self, children: list[Any]) -> TerminalSpec:
        """Build a ``TerminalSpec`` from name and delimited pattern.

        children: [name_str, pattern_lexeme, ";"]

        ``/regex/`` patterns are used as-is; ``"literal"`` patterns are
        passed through ``re.escape`` so they match exactly.
        """
        name: str = children[0]
        lexeme: str = children[1]
        if lexeme.startswith('"'):
            pattern = re.escape(lexeme[1:-1])
        else:
            pattern = lexeme[1:-1]
        return TerminalSpec(name=name, pattern=pattern)

    def ignore_section(self, children: list[Any]) -> list[str]:
        """Return the list of ignored terminal name strings.

        children: [".IGNORE", names_list, ";"]
        """
        return children[1]

    def ignore_names(self, children: list[Any]) -> list[str]:
        """Incrementally build the ignored-names list from left-recursive children.

        children: [word_str] for base case, or [prev_list, word_str] for recursive.
        """
        if len(children) == 1:
            return [children[0]]
        return children[0] + [children[1]]
