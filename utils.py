def flatten(arr):
    if isinstance(arr, list):
        return [item for sublist in arr for item in flatten(sublist)]
    return [arr]


def print_states(states):
    for index, state in enumerate(states):
        print(f"STATE_{index}:")
        for item in state.items:
            production = f"{item.production.lhs} ::= {' '.join(item.production.rhs[:item.dot] + ['.'] + item.production.rhs[item.dot:])} ({str(list(item.lookahead))})"
            print(f"\t{production}")