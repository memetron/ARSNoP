import re
from collections.abc import Sequence
from typing import NoReturn

from arsnop.grammar.bnf_types import TerminalSpec

from .token import Token


class Lexer:
    def __init__(self, terminals: Sequence[TerminalSpec], ignored: Sequence[str]) -> None:
        self.terminals: dict[str, TerminalSpec] = {spec.name: spec for spec in terminals}
        self._compiled: dict[str, re.Pattern[str]] = {
            spec.name: re.compile(spec.pattern) for spec in terminals
        }
        self.ignored: list[str] = list(ignored)

    def lex_one(self, text: str, pos: int, valid: frozenset[str]) -> tuple[Token | None, int]:
        """Match the next meaningful token at position pos, only trying terminals in `valid`.

        Ignored terminals are always skipped transparently before matching.
        Returns (None, pos) when end of input is reached after skipping trailing ignored.
        Raises Exception if stuck at an unmatchable position.
        """
        pos = self._skip_ignored(text, pos)
        if pos >= len(text):
            return None, pos
        name, length = self._best_match(text, pos, valid)
        if not name:
            _raise_lex_error(text, pos, valid)
        spec = self.terminals[name]
        return Token(name, text[pos : pos + length], inline=spec.inline), pos + length

    def _skip_ignored(self, text: str, pos: int) -> int:
        """Advance pos past any sequence of ignored terminals."""
        advanced = True
        while advanced and pos < len(text):
            advanced = False
            for name in self.ignored:
                m = self._compiled[name].match(text, pos)
                if m:
                    pos = m.end()
                    advanced = True
                    break
        return pos

    def _best_match(self, text: str, pos: int, valid: frozenset[str]) -> tuple[str, int]:
        """Return (name, length) of the longest valid terminal matching at pos.

        Iterates in definition order so earlier-defined terminals win ties.
        Returns ("", 0) if nothing matches.
        """
        best_len = 0
        best_name = ""
        for name in self._compiled:
            if name in valid:
                m = self._compiled[name].match(text, pos)
                if m and len(m.group()) > best_len:
                    best_len = len(m.group())
                    best_name = name
        return best_name, best_len


def _raise_lex_error(text: str, pos: int, valid: frozenset[str]) -> NoReturn:
    line = text.count("\n", 0, pos) + 1
    col = pos - text.rfind("\n", 0, pos)
    char = repr(text[pos])
    expected = ", ".join(sorted(valid)) if valid else "nothing"
    raise Exception(
        f"Unexpected character {char} at line {line}, column {col}"
        f" (expected: {expected})"
    )
