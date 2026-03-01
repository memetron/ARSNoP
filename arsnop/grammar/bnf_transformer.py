"""Transformer that converts a BNF parse tree into typed ``BnfSpec`` objects.

The BNF grammar is left-recursive, so the Earley AST uses left-associative
trees for all list-like constructs.  Each visitor method receives the already-
transformed children and incrementally builds the result.
"""
from __future__ import annotations

import re
from typing import Any

from ..transformer import Transformer
from .bnf_types import Modifier, Rhs, BnfSpec, RuleSpec, TerminalSpec

_MODIFIER_SUFFIX: dict[str, str] = {"?": "opt", "*": "star", "+": "plus"}


class BnfSpecTransformer(Transformer):
    """Transforms a BNF parse tree into ``BnfSpec`` (and its component types).

    Supports EBNF modifiers (``?``, ``*``, ``+``) by desugaring them into
    auxiliary BNF rules appended to the spec:

    - ``A?``  →  ``_A_opt  ::= A | ;``
    - ``A*``  →  ``_A_star ::= _A_star A | ;``
    - ``A+``  →  ``_A_plus ::= _A_plus A | A ;``

    Override individual visit methods — the base ``Transformer`` dispatches
    by node name via ``getattr``.
    """

    def __init__(self) -> None:
        self._aux_rules: dict[str, RuleSpec] = {}

    def bnf_file(self, children: list[Any]) -> BnfSpec:
        """Combine rules and terminals sections into a ``BnfSpec``.

        children: [":GRAMMAR", rules_list, ":TERMINALS", (terminals, ignored)]

        Any auxiliary rules generated from EBNF modifiers are appended after
        the user-defined rules.
        """
        rules: list[RuleSpec] = children[1]
        terminals: list[TerminalSpec]
        ignored: list[str]
        terminals, ignored = children[3]
        return BnfSpec(
            rules=tuple(rules) + tuple(self._aux_rules.values()),
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
        alternatives: list[Rhs] = children[2]
        return RuleSpec(lhs=lhs, alternatives=tuple(alternatives))

    def alternatives(self, children: list[Any]) -> list[Rhs]:
        """Incrementally build the alternatives list from left-recursive children.

        children: [alt] for base case, or [alts_list, "|", alt] for recursive.
        """
        if len(children) == 1:
            return [children[0]]
        return children[0] + [children[2]]

    def _desugar(self, id_str: str, modifier: str) -> str:
        """Return the aux-rule name for ``id_str`` modified by ``modifier``.

        Generates and caches the corresponding BNF rule on first call:

        - ``?``  →  ``_X_opt  ::= X | ;``
        - ``*``  →  ``_X_star ::= _X_star X | ;``
        - ``+``  →  ``_X_plus ::= _X_plus X | X ;``
        """
        aux_name = f"_{id_str}_{_MODIFIER_SUFFIX[modifier]}"
        if aux_name not in self._aux_rules:
            if modifier == "?":
                rule = RuleSpec(aux_name, (Rhs((id_str,)), Rhs(())), Modifier.OPT)
            elif modifier == "*":
                rule = RuleSpec(aux_name, (Rhs((aux_name, id_str)), Rhs(())), Modifier.STAR)
            else:  # "+"
                rule = RuleSpec(aux_name, (Rhs((aux_name, id_str)), Rhs((id_str,))), Modifier.PLUS)
            self._aux_rules[aux_name] = rule
        return aux_name

    def alternative(self, children: list[Any]) -> Rhs:
        """Build an ``Alternative`` incrementally from left-recursive children.

        children: [] for empty base case, [prev_alt, id_str] for a plain
        symbol, or [prev_alt, id_str, modifier] for an EBNF modifier.
        """
        if not children:
            return Rhs(symbols=())
        prev: Rhs = children[0]
        id_str: str = children[1]
        if len(children) == 3:
            modifier: str = children[2]
            return Rhs(symbols=prev.symbols + (self._desugar(id_str, modifier),))
        return Rhs(symbols=prev.symbols + (id_str,))

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

        children: [id_str] for base case, or [prev_list, id_str] for recursive.
        """
        if len(children) == 1:
            return [children[0]]
        return children[0] + [children[1]]
