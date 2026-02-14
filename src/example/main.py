from pprint import pprint

from ..parser.parser import from_file
from .timformer import Timformer


def main():
    earley = from_file('src/resources/grammar.bnf', parser="earley", transformer=Timformer())
    with open('src/resources/text.tim', 'r') as file:
        text = file.read()
    tree = earley.parse(text)
    pprint(tree)
if __name__ == "__main__":
    main()