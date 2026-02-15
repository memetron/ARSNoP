from typing import Literal

from ...grammar import Production

type GotoTable = dict[tuple[int, str], int]
type ShiftAction = tuple[Literal["shift"], int]
type ReduceAction = tuple[Literal["reduce"], Production]
type AcceptAction = tuple[Literal["accept"]]
type Action = ShiftAction | ReduceAction | AcceptAction
type ActionTable = dict[tuple[int, str], Action]
