"""Checks shared by the tool verifiers. Pure functions of their arguments.

The shortest-route search here is the verifier's own, written out again rather than imported: the
verifier may not import the plugin, and it should not take the reference tool's word for what the
cheapest route costs. tests/test_maps.py holds the two searches in step.
"""

from itertools import pairwise

LONGEST_ROUTE = 100


def result(valid, message, *, score=None, **details):
    return {
        "valid": valid,
        "score": float(valid) if score is None else score,
        "message": message,
        "details": details,
    }


def links_problem(links, label):
    """What is wrong with ``links`` as a map, or None."""
    if not links:
        return f"{label} must hold at least one link"
    seen = set()
    for link in links:
        if not link.start or not link.end:
            return f"{label} has a link with an unnamed end"
        if link.start == link.end:
            return f"{label} has a link from {link.start} to itself"
        if link.cost <= 0:
            return f"{label} has a link {link.start}-{link.end} costing {link.cost}, which is not above zero"
        pair = frozenset((link.start, link.end))
        if pair in seen:
            return f"{label} names the link between {link.start} and {link.end} twice"
        seen.add(pair)
    return None


def costs_of(links):
    """{(one end, other end): cost} for ``links``, both ways round."""
    both = {}
    for link in links:
        both[(link.start, link.end)] = link.cost
        both[(link.end, link.start)] = link.cost
    return both


def nodes_of(links):
    return {node for link in links for node in (link.start, link.end)}


def lowest_cost(links, start, goal):
    """What the cheapest route from ``start`` to ``goal`` costs, or None when there is none."""
    costs = costs_of(links)
    nodes = nodes_of(links)
    if start not in nodes or goal not in nodes:
        return None
    far = {node: None for node in nodes}
    far[start] = 0
    left = set(nodes)
    while left:
        reached = [node for node in left if far[node] is not None]
        if not reached:
            break
        here = min(reached, key=lambda node: far[node])
        left.discard(here)
        for head in left:
            cost = costs.get((here, head))
            if cost is None:
                continue
            through = far[here] + cost
            if far[head] is None or through < far[head]:
                far[head] = through
    return far[goal]


def route_problem(route, links, start, goal, label):
    """What is wrong with ``route`` as a route over ``links`` from ``start`` to ``goal``, or None."""
    if not route:
        return f"{label} must name at least one node"
    if len(route) > LONGEST_ROUTE:
        return f"{label} must cross at most {LONGEST_ROUTE} nodes, not {len(route)}"
    if len(set(route)) != len(route):
        return f"{label} passes through a node twice"
    if route[0] != start:
        return f"{label} starts at {route[0]}, not {start}"
    if route[-1] != goal:
        return f"{label} ends at {route[-1]}, not {goal}"
    costs = costs_of(links)
    for tail, head in pairwise(route):
        if (tail, head) not in costs:
            return f"{label} steps from {tail} to {head}, and the map has no such link"
    return None


def route_cost(route, links):
    """What ``route`` costs over ``links``; only call it once route_problem has passed."""
    costs = costs_of(links)
    return sum(costs[(tail, head)] for tail, head in pairwise(route))
