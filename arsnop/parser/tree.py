"""Shared helpers for building ASTs that inline EBNF-generated nodes.

Both the Earley and shift-reduce parsers desugar EBNF modifiers (``?``, ``*``,
``+``) into auxiliary BNF rules.  When constructing the AST they use the same
two-step pattern:

1. **splice_children** — when collecting a node's children, any child that is
   itself an inline-generated node is spliced in-place (its items extend the
   parent's child list) rather than being appended as a wrapper node.
2. **make_tree_item** — when emitting a node for a completed rule, inline
   rules return a bare ``list[AST]`` (to be spliced by their parent) while
   normal rules return a proper ``AST`` node.
"""
from __future__ import annotations

from collections.abc import Iterable

from ..ast import AST

type TreeItem = AST | list[AST]


def splice_children(items: Iterable[TreeItem]) -> list[AST]:
    """Flatten inline modifier lists into a contiguous child list.

    Each item that is a ``list[AST]`` (produced by a modifier rule) has its
    elements extended into the result; plain ``AST`` items are appended as-is.
    """
    children: list[AST] = []
    for item in items:
        if isinstance(item, list):
            children.extend(item)
        else:
            children.append(item)
    return children


def make_tree_item(lhs: str, inline: bool, children: list[AST]) -> TreeItem:
    """Return an ``AST`` node for normal rules, or a bare list for inline rules.

    The bare list is later spliced into the parent by ``splice_children``,
    leaving no wrapper node for EBNF-generated rules in the final tree.
    """
    if inline:
        return children
    return AST(lhs, children)
