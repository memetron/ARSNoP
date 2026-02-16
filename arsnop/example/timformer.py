from typing import Any

from ..transformer import Transformer
from ..utils import flatten


class Timformer(Transformer):
    def value(self, children: list[Any]) -> Any:
        return children[0]

    def start(self, children: list[Any]) -> Any:
        return children[0]

    def body(self, children: list[Any]) -> Any:
        return {
            "global_conf": children[0],
            "object_list": children[2],
            "player_info": children[3]
        }

    def global_conf(self, children: list[Any]) -> Any:
        return children[1]  # conf_list

    def conf_list(self, children: list[Any]) -> Any:
        return children

    def conf_option(self, children: list[Any]) -> Any:
        key = children[0]
        value = children[2]
        return {key: value}

    def obj_list(self, children: list[Any]) -> Any:
        return children

    def object(self, children: list[Any]) -> Any:
        return {
            "id": children[0],
            "type": children[2],
            "properties": flatten(children[3]),
            "scale": children[4],
            "position": children[5],
            "orientation": children[6],
            "textureInfo": children[7]
        }

    def type(self, children: list[Any]) -> Any:
        return children[2]

    def properties(self, children: list[Any]) -> Any:
        return children[3]

    def prop_list(self, children: list[Any]) -> Any:
        return children

    def scale(self, children: list[Any]) -> Any:
        return float(children[2])

    def textureInfo(self, children: list[Any]) -> Any:
        return children[3]

    def player_info(self, children: list[Any]) -> Any:
        return {
            "position": children[1],
            "orientation": children[2]
        }

    def position(self, children: list[Any]) -> Any:
        return children[3]

    def pos(self, children: list[Any]) -> Any:
        return tuple(map(float, children))

    def orientation(self, children: list[Any]) -> Any:
        return children[3]

    def rot(self, children: list[Any]) -> Any:
        return tuple(map(float, children))

    def int_list(self, children: list[Any]) -> Any:
        return list(map(int, children))
