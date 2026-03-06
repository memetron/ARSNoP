from pprint import pprint

from arsnop.example.arithmetic_transformer import ArithmeticTransformer

from ..parser import from_file


def main() -> None:
    earley = from_file('arsnop/resources/arithmetic.bnf', parser="earley", transformer=ArithmeticTransformer())
    expr = input("Enter an arithmetic expression: ")
    result = earley.parse(expr)
    pprint(result)

if __name__ == "__main__":
    main()