"""Each case's map, and the shortest route across it.

The maps are small on purpose: a few calls to neighbours map one out, so the work is exploring
under partial sight rather than outlasting a long loop. Links are undirected and every cost is
above zero, so a shortest route never visits a node twice.
"""

from __future__ import annotations

from contract import Case

# case -> (start, goal, [(one end, other end, cost), ...]). Each link is written once.
MAPS = {
    # One shortest route, and the cheapest first step happens to be on it.
    Case.ORCHARD: (
        "A",
        "F",
        [
            ("A", "B", 4), ("A", "C", 2), ("B", "D", 5), ("C", "B", 1), ("C", "D", 8),
            ("C", "E", 10), ("D", "E", 2), ("D", "F", 6), ("E", "F", 3),
        ],
    ),
    # Two different routes are both shortest, so the check cannot compare against one answer.
    Case.QUARRY: (
        "A",
        "E",
        [
            ("A", "B", 3), ("A", "C", 3), ("B", "D", 4), ("C", "D", 4),
            ("D", "E", 2), ("A", "E", 10), ("C", "F", 1),
        ],
    ),
    # The cheapest first step leads away from the shortest route.
    Case.FOUNDRY: (
        "A",
        "G",
        [
            ("A", "B", 1), ("B", "C", 1), ("C", "G", 20), ("A", "D", 5),
            ("D", "E", 2), ("E", "G", 2), ("B", "F", 1), ("F", "E", 6),
        ],
    ),
    # Larger, and the shortest route runs through almost every node.
    Case.HARBOUR: (
        "A",
        "H",
        [
            ("A", "B", 2), ("A", "C", 5), ("B", "C", 2), ("B", "D", 7), ("C", "D", 3),
            ("C", "E", 6), ("D", "E", 1), ("D", "F", 4), ("E", "F", 2), ("E", "G", 8),
            ("F", "G", 3), ("G", "H", 2), ("F", "H", 9),
        ],
    ),
}


def nodes_of(case: Case) -> list[str]:
    """Every node on ``case``'s map, in the order the links first name them."""
    _, _, links = MAPS[case]
    seen: list[str] = []
    for one, other, _ in links:
        for node in (one, other):
            if node not in seen:
                seen.append(node)
    return sorted(seen)


def links_touching(case: Case, nodes: list[str]) -> list[tuple[str, str, int]]:
    """``case``'s links with an end among ``nodes``, each one once, in the map's own order."""
    unknown = [node for node in nodes if node not in nodes_of(case)]
    if unknown:
        raise ValueError(f"no such node on the {case.value} map: {unknown}")
    _, _, links = MAPS[case]
    wanted = set(nodes)
    return [link for link in links if link[0] in wanted or link[1] in wanted]


def cheapest(case: Case) -> tuple[list[str], int]:
    """A cheapest route from ``case``'s start to its goal, and what it costs."""
    start, goal, links = MAPS[case]
    far = {node: None for node in nodes_of(case)}  # None stands for "no route found yet"
    far[start] = 0
    came: dict[str, str] = {}
    left = set(far)
    while left:
        here = min((node for node in left if far[node] is not None), key=lambda node: far[node], default=None)
        if here is None:
            break
        left.discard(here)
        for one, other, cost in links:
            for tail, head in ((one, other), (other, one)):
                if tail != here or head not in left:
                    continue
                through = far[here] + cost
                if far[head] is None or through < far[head]:
                    far[head] = through
                    came[head] = here
    if far[goal] is None:
        raise ValueError(f"the {case.value} map has no route from {start} to {goal}")
    route = [goal]
    while route[-1] != start:
        route.append(came[route[-1]])
    return list(reversed(route)), far[goal]
