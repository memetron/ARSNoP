from __future__ import annotations

from typing import TypeVar, ParamSpec, Callable, Protocol, Concatenate
from functools import wraps


S = TypeVar("S")
P = ParamSpec("P")


class FixedPointStep(Protocol[S, P]):
    def __call__(self, state: S, *args: P.args, **kwargs: P.kwargs) -> S: ...


def fixed_point(
    func: Callable[Concatenate[S, P], S],
) -> Callable[Concatenate[S, P], S]:
    """
    Repeatedly applies a pure transformation until a fixed point is reached.

    The decorated function must:
        - Treat `state` as immutable
        - Return a *new* state
        - Eventually converge under equality

    Stops when:
        new_state == state
    """

    @wraps(func)
    def wrapper(state: S, *args: P.args, **kwargs: P.kwargs) -> S:
        current: S = state

        while True:
            new_state: S = func(current, *args, **kwargs)

            if new_state == current:
                return current

            current = new_state

    return wrapper