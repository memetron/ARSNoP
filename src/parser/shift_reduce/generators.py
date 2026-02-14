from ...grammar import Grammar
from .automaton import Automaton
from .state import lr0_states, lr1_states, merge_lr1_states, lalr_states


class Generator:
    """
    Base class for parsing table shift_reduce.
    Methods:
        generate(grammar: Grammar): Abstract method to be implemented by subclasses for generating
            an automaton based on the provided grammar
    """
    def generate(self, grammar: Grammar) -> Automaton:
        raise NotImplementedError()


class LR0(Generator):
    """
    Class for generating LR(0) parsing tables.
    Methods:
        generate(grammar: Grammar): Generates LR(0) automaton
    """
    def generate(self, grammar: Grammar):
        goto = {}
        action = {}
        states, transitions = lr0_states(grammar)

        for i, state in enumerate(states):
            for item in state.items:
                if item.dot == len(item.production.rhs):  # Reduce or Accept state
                    if item.production.lhs == "S'":
                        action[(i, '$')] = ("accept",)
                    else:
                        for terminal in grammar.terminals | {'$'}:
                            action[(i, terminal)] = ("reduce", item.production)
                elif item.dot < len(item.production.rhs):  # Shift state
                    symbol = item.production.rhs[item.dot]
                    if symbol in grammar.terminals:
                        next_state = transitions.get((i, symbol))
                        if next_state is not None:
                            action[(i, symbol)] = ("shift", next_state)

            for non_terminal in grammar.non_terminals:
                next_state = transitions.get((i, non_terminal))
                if next_state is not None:
                    goto[(i, non_terminal)] = next_state

        return Automaton(goto, action)


class LR1(Generator):
    """
    Class for generating LR(1) parsing tables.
    Methods:
        generate(grammar: Grammar): Generates LR(1) automaton.
    """
    def generate(self, grammar: Grammar):
        goto = {}
        action = {}
        states, transitions = lr1_states(grammar)

        for i, state in enumerate(states):
            for item in state.items:
                if item.dot == len(item.production.rhs):  # Reduce or Accept state
                    if item.production.lhs == "S'":
                        action[(i, '$')] = ("accept",)
                    else:
                        for terminal in item.lookahead:
                            action[(i, terminal)] = ("reduce", item.production)
                elif item.dot < len(item.production.rhs):  # Shift state
                    symbol = item.production.rhs[item.dot]
                    if symbol in grammar.terminals:
                        next_state = transitions.get((i, symbol))
                        if next_state is not None:
                            action[(i, symbol)] = ("shift", next_state)

            for non_terminal in grammar.non_terminals:
                next_state = transitions.get((i, non_terminal))
                if next_state is not None:
                    goto[(i, non_terminal)] = next_state

        return Automaton(goto, action)


class SLR(Generator):
    """
    Class for generating SLR(1) parsing tables.
    Methods:
        generate(grammar: Grammar): Generates SLR(1) automaton.
    """
    def generate(self, grammar: Grammar):
        goto = {}
        action = {}
        states, transitions = lr0_states(grammar)

        for i, state in enumerate(states):
            for item in state.items:
                if item.dot == len(item.production.rhs):  # Reduce or Accept state
                    if item.production.lhs == "S'":
                        action[(i, '$')] = ("accept",)
                    else:
                        for terminal in grammar.follow(item.production.lhs):
                            action[(i, terminal)] = ("reduce", item.production)
                elif item.dot < len(item.production.rhs):  # Shift state
                    symbol = item.production.rhs[item.dot]
                    if symbol in grammar.terminals:
                        next_state = transitions.get((i, symbol))
                        if next_state is not None:
                            action[(i, symbol)] = ("shift", next_state)

            for non_terminal in grammar.non_terminals:
                next_state = transitions.get((i, non_terminal))
                if next_state is not None:
                    goto[(i, non_terminal)] = next_state

        return Automaton(goto, action)


class LALR_Brute_Force(Generator):
    """
    Class for generating LALR(1) parsing tables.
    Creates the tables via brute force merging LR(1) states
    Methods:
        generate(grammar: Grammar): Generates LALR(1) automaton.
    """
    def generate(self, grammar: Grammar):
        goto = {}
        action = {}
        states, transitions = merge_lr1_states(*lr1_states(grammar))
        for i, state in enumerate(states):
            for item in state.items:
                if item.dot == len(item.production.rhs):  # Reduce or Accept state
                    if item.production.lhs == "S'":
                        action[(i, '$')] = ("accept",)
                    else:
                        for terminal in item.lookahead:
                            action[(i, terminal)] = ("reduce", item.production)
                elif item.dot < len(item.production.rhs):  # Shift state
                    symbol = item.production.rhs[item.dot]
                    if symbol in grammar.terminals:
                        next_state = transitions.get((i, symbol))
                        if next_state is not None:
                            action[(i, symbol)] = ("shift", next_state)

            for non_terminal in grammar.non_terminals:
                next_state = transitions.get((i, non_terminal))
                if next_state is not None:
                    goto[(i, non_terminal)] = next_state
        return Automaton(goto, action)


class LALR(Generator):
    """
    Class for generating LALR(1) parsing tables.
    Creates the tables by merging LR(1) states as they are generated
    Methods:
        generate(grammar: Grammar): Generates LALR(1) automaton.
    """
    def generate(self, grammar: Grammar):
        goto = {}
        action = {}
        states, transitions = lalr_states(grammar)

        for i, state in enumerate(states):
            for item in state.items:
                if item.dot == len(item.production.rhs):  # Reduce or Accept state
                    if item.production.lhs == "S'":
                        action[(i, '$')] = ("accept",)
                    else:
                        for terminal in item.lookahead:
                            action[(i, terminal)] = ("reduce", item.production)
                elif item.dot < len(item.production.rhs):  # Shift state
                    symbol = item.production.rhs[item.dot]
                    if symbol in grammar.terminals:
                        next_state = transitions.get((i, symbol))
                        if next_state is not None:
                            action[(i, symbol)] = ("shift", next_state)

            for non_terminal in grammar.non_terminals:
                next_state = transitions.get((i, non_terminal))
                if next_state is not None:
                    goto[(i, non_terminal)] = next_state

        return Automaton(goto, action)
