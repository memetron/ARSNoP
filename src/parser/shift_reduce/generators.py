from ...grammar import Grammar
from .automaton import Automaton


class Generator:
    """
    Base class for parsing table shift_reduce.
    Methods:
        generate(grammar: Grammar): Abstract method to be implemented by subclasses for generating
            an automaton based on the provided grammar
    """
    def generate(self, grammar: Grammar) -> Automaton:
        raise NotImplementedError()
