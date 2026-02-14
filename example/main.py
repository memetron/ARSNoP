from pprint import pprint

from src.parser.parser import from_file
from timformer import Timformer


def main():
    earley = from_file('resources/grammar.bnf', parser="lr0", transformer=Timformer())
    with open('resources/text.tim', 'r') as file:
        text = file.read()
    tree = earley.parse(text)
    pprint(tree)
if __name__ == "__main__":
    main()