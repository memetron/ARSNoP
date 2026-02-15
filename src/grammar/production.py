class Production:
    """
    A class to represent a production rule in a context-free grammar.
    Attributes:
        lhs (str): The left-hand side of the production rule, which must be a non-terminal.
        rhs (list[str]): The right-hand side of the production rule, which is a list of symbols (terminals or non-terminals).
    """

    def __init__(self, lhs: str, rhs: list[str]) -> None:
        """
        Initializes a production rule with a left-hand side and a right-hand side.
        Args:
            lhs (str): The non-terminal on the left-hand side of the production rule.
            rhs (list[str]): A list of symbols on the right-hand side of the production rule.
        """
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self) -> str:
        return f"{self.lhs} ::= {' '.join(self.rhs)}"