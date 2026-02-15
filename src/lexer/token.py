class Token:
    """
    A class to represent a token in lexical analysis.
    Attributes:
        token (str): The type of the token, representing its classification (e.g., "IDENTIFIER", "NUMBER").
        lexeme (str): The actual string of characters matched in the input text.
    """

    def __init__(self, token: str, lexeme: str) -> None:
        """
        Initializes a Token object with a type and its corresponding lexeme.
        Args:
            token (str): The type of the token, typically corresponding to a terminal symbol in a grammar.
            lexeme (str): The actual string matched from the input text.
        """
        self.token = token
        self.lexeme = lexeme

    def __str__(self) -> str:
        return f"token({self.token}, \"{self.lexeme}\")"
