from __future__ import annotations

from typing import Literal, Final
from ...grammar import Production
    
type GotoTable = dict[tuple[int, str], int]
type ShiftAction = tuple[Literal["shift"], int]
type ReduceAction = tuple[Literal["reduce"], Production]
type AcceptAction = tuple[Literal["accept"]]
type Action = ShiftAction | ReduceAction | AcceptAction
type ActionTable = dict[tuple[int, str], Action]
type Kernel = frozenset[tuple[Production, int]]
type StateIndex = int
type KernelItem = tuple[StateIndex, tuple[Production, int]]
type LookaheadSet = set[str]
type LookaheadTable = dict[KernelItem, LookaheadSet]
type PropagationGraph = dict[KernelItem, set[KernelItem]]
FAKE: Final[str] = "#"