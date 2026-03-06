from typing import Any

from ..transformer import Transformer


class ArithmeticTransformer(Transformer):
    def start(self, children: list[Any]) -> Any:
        return children[0]

    def addition(self, children: list[Any]) -> float:
        return float(children[0]) + float(children[1])

    def multiplication(self, children: list[Any]) -> float:
        return float(children[0]) * float(children[1])

    def division(self, children: list[Any]) -> float:
        return float(children[0]) / float(children[1])

    def subtraction(self, children: list[Any]) -> float:
        return float(children[0]) - float(children[1])
