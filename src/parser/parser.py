import re

from src.grammar.grammar import Grammar
from src.lexer.lexer import Lexer
from src.parser.earley.earley import Earley
from src.parser.parsingEngine import ParsingEngine
from src.parser.shift_reduce.generators import SLR, LALR_Brute_Force, LALR, LR1, LR0
from src.transformer.transformer import Transformer

# Regular expression to extract grammar and terminals from a text file
_GRAMMAR_FORMAT = re.compile(r":GRAMMAR(.*):TERMINALS(.*)", re.DOTALL)

def from_file(file_path: str, parser="earley", transformer: Transformer = None):
    """
    Creates a Parser instance from a grammar definition file.

    Args:
        file_path (str): The path to the grammar definition file.
        parser (str): The parser algorithm to use. Options include:
                      "earley", "lalr", "lalr_brute_force", "SLR", "LR1", "LR0".
                      Default is "Earley".
        transformer (Transformer, optional): A Transformer instance to transform the resulting AST. Default is None.

    Returns:
        Parser: An initialized Parser instance.

    Raises:
        Exception: If the parser name is invalid or not supported.

    File Format:
        The input file should contain two sections:
            1. A ":GRAMMAR" section with the grammar rules.
            2. A ":TERMINALS" section with terminal definitions.
            3. An ".IGNORE" section with terminals to ignore

    Example:
        :GRAMMAR
        s ::= a b
        a ::= A
        b ::= B
        :TERMINALS
        A a
        B b
        .IGNORE
        A
    """
    with open(file_path, 'r') as file:
        text = file.read()
    grammar, terminals = re.match(_GRAMMAR_FORMAT, text).groups()
    grammar = Grammar(grammar)
    lexer = Lexer(terminals)

    if parser == "earley":
        generated = Earley(grammar)
    elif parser == "lalr":
        generated = LALR().generate(grammar)
    elif parser == "lalr_brute_force":
        generated = LALR_Brute_Force().generate(grammar)
    elif parser == "slr":
        generated = SLR().generate(grammar)
    elif parser == "lr1":
        generated = LR1().generate(grammar)
    elif parser == "lr0":
        generated = LR0().generate(grammar)
    else:
        raise Exception("Invalid parser name")

    return Parser(lexer, generated, transformer)

class Parser:
    """
    A class for parsing input text based on a context-free grammar.

    Methods:
        parse(text: str):
            Parses the input text and returns the transformed AST or raw AST.
    """

    def __init__(self, lexer: Lexer, parser: ParsingEngine, transformer: Transformer = None):
        """
        Initializes the Parser instance.

        Args:
            lexer (Lexer): The lexer instance for tokenizing input text.
            parser (ParsingEngine): The parsing engine instance.
            transformer (Transformer, optional): An optional transformer for processing the AST. Default is None.
        """
        self._transformer = transformer
        self._lexer = lexer
        self._parser = parser

    def parse(self, text: str):
        """
        Parses the input text and generates an Abstract Syntax Tree (AST).

        Args:
            text (str): The input text to parse.

        Returns:
            Any: The transformed AST if a transformer is provided, or the raw AST otherwise.
        """
        tokens = self._lexer.lex(text)
        ast = self._parser.parse(tokens)
        return self._transformer.transform(ast) if self._transformer else ast
