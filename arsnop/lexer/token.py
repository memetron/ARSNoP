class Token:
    """
    A class to represent a token in lexical analysis.
    Attributes:
        token (str): The type of the token, representing its classification (e.g., "IDENTIFIER", "NUMBER").
        lexeme (str): The actual string of characters matched in the input text.
    """

    def __init__(self, token: str, lexeme: str, inline: bool = False) -> None:
        """
        Initializes a Token object with a type and its corresponding lexeme.
        Args:
            token (str): The type of the token, typically corresponding to a terminal symbol in a grammar.
            lexeme (str): The actual string matched from the input text.
            inline (bool): Whether the token is an inline terminal.
        """
        self.token = token
        self.lexeme = lexeme
        self.inline = inline

    def __str__(self) -> str:
        return f"token({self.token}, \"{self.lexeme}\")"
