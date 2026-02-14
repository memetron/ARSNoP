import re
import functools

from .production import Production

_RULE_REGEX = re.compile(r"^(.+)::=(.+)$")


class Grammar:
    """
    A class to represent a context-free grammar, compute FIRST and FOLLOW sets, and perform LR item closure and state transitions.
    Attributes:
        terminals (Set[str]): A set of terminal symbols in the grammar.
        non_terminals (Set[str]): A set of non-terminal symbols in the grammar.
        productions (List[Production]): A list of grammar productions.
        start_symbol (str): The start symbol of the grammar.
    Methods:
        __init__(text: str, start_symbol: str = "start"):
            Initializes the grammar by parsing the input grammar text.

        lookup_productions(non_terminal: str) -> List[Production]:
            Retrieves the productions for a given non-terminal symbol.
        is_nullable(non_terminal: str) -> bool:
            Checks if a non-terminal can derive the empty string (ε).
        first(symbol: str) -> Set[str]:
            Computes the FIRST set of a given symbol.
        follow(symbol: str) -> Set[str]:
            Computes the FOLLOW set of a given non-terminal symbol.
        closure(items: List[Tuple[Production, int]]) -> List[Tuple[Production, int]]:
            Computes the closure of a set of LR items.
        successor(items: List[Tuple[Production, int]], symbol: str) -> List[Tuple[Production, int]]:
            Computes the successor state after shifting a given symbol in a set of LR items.
    """
    terminals: set[str]
    non_terminals: set[str]
    productions: list[Production]
    start_symbol: str

    def __init__(self, text, start_symbol="start"):
        """
        Initializes the Grammar object.
        Args:
            text (str): A string representation of the grammar, where each rule is of the form `A ::= B | C`.
            start_symbol (str, optional): The start symbol of the grammar. Defaults to "start".
        """
        self.productions = []
        self.terminals = set()
        self.non_terminals = set()
        self.start_symbol = start_symbol

        for rule in text.strip().split('\n'):
            match = re.match(_RULE_REGEX, rule)
            if match:
                non_terminal, rule_definitions = match.groups()
                non_terminal = non_terminal.strip()
                self.non_terminals.add(non_terminal)

                rule_parts = [r.split() for r in rule_definitions.split('|')]
                for rule_part in rule_parts:
                    self.productions.append(Production(non_terminal, rule_part))
                    for symbol in rule_part:
                        self.terminals.add(symbol)

        self.terminals -= self.non_terminals

    @functools.cache
    def lookup_productions(self, non_terminal: str):
        """
        Retrieves the productions for a given non-terminal.
        Args:
            non_terminal (str): The non-terminal whose productions are to be retrieved.
        Returns:
            List[Production]: A list of productions with the specified non-terminal as the left-hand side.
        """
        return [production for production in self.productions if production.lhs == non_terminal]

    @functools.cache
    def is_nullable(self, non_terminal: str) -> bool:
        """
        Determines if a non-terminal can derive the empty string (ε).
        Args:
            non_terminal (str): The non-terminal to check.
        Returns:
            bool: True if the non-terminal can derive ε, otherwise False.
        """
        return [] in self.lookup_productions(non_terminal)

    def first(self, symbol: str) -> set[str]:
        """
        Computes the FIRST set for a given symbol. The first set is defined as the set of terminals that can exist
        first when expanding a given symbol.
        Args:
            symbol (str): The symbol whose FIRST set is to be computed.
        Returns:
            Set[str]: The FIRST set of the given symbol.
        """
        return self._first_dict()[symbol]

    @functools.cache
    def _first_dict(self):
        first_sets = {s: set() for s in self.terminals.union(self.non_terminals)}
        for terminal in self.terminals:
            first_sets[terminal].add(terminal)
        while True:
            # fixed-point iteration
            updated = False
            for production in self.productions:
                lhs = production.lhs
                for rhs_symbol in production.rhs:
                    new_firsts = first_sets[rhs_symbol] - {''}
                    if not new_firsts.issubset(first_sets[lhs]):
                        first_sets[lhs].update(new_firsts)
                        updated = True
                    if '' not in first_sets[rhs_symbol]:
                        break
                else:
                    if '' not in first_sets[lhs]:
                        first_sets[lhs].add('')
                        updated = True
            if not updated:
                break
        return first_sets

    def follow(self, symbol: str) -> set[str]:
        """
        Computes the FOLLOW set for a given non-terminal. The follow set is defined as the set of terminals that
        can exist immediately after a non-terminal.
        Args:
            symbol (str): The non-terminal whose FOLLOW set is to be computed.
        Returns:
            Set[str]: The FOLLOW set of the given non-terminal.
        """
        return self._follow_dict()[symbol]

    @functools.cache
    def _follow_dict(self):
        follow_sets = {nt: set() for nt in self.non_terminals}
        follow_sets[self.start_symbol].add('$')
        while True:
            # fixed-point iteration
            updated = False
            for production in self.productions:
                lhs = production.lhs
                for i, part in enumerate(production.rhs):
                    if part in self.non_terminals:
                        follow = set()
                        for next_part in production.rhs[i + 1:]:
                            follow.update(self.first(next_part) - {''})
                            if '' not in self.first(next_part):
                                break
                        else:
                            follow.update(follow_sets[lhs])
                        if not follow.issubset(follow_sets[part]):
                            follow_sets[part].update(follow)
                            updated = True
            if not updated:
                break
        return follow_sets
