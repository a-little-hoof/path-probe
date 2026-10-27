"""The invariants the design rests on: the two searches agree, and each map has the character
the task needs it to have."""

from __future__ import annotations

import pytest

from contract import Case
from plugin.maps import MAPS, cheapest, links_touching, nodes_of
from verifier.checks import links_problem, lowest_cost, route_cost, route_problem


class Edge:
    """A stand-in for contract.Link, so the verifier's checks can be run on the raw map."""

    def __init__(self, start: str, end: str, cost: int) -> None:
        self.start, self.end, self.cost = start, end, cost


def edges(case: Case) -> list[Edge]:
    return [Edge(one, other, cost) for one, other, cost in MAPS[case][2]]


def every_route(case: Case) -> list[tuple[int, list[str]]]:
    """Every simple route from start to goal, found by exhaustive search rather than Dijkstra."""
    start, goal, links = MAPS[case]
    near: dict[str, list[tuple[str, int]]] = {}
    for one, other, cost in links:
        near.setdefault(one, []).append((other, cost))
        near.setdefault(other, []).append((one, cost))
    found: list[tuple[int, list[str]]] = []

    def walk(here: str, seen: list[str], cost: int) -> None:
        if here == goal:
            found.append((cost, list(seen)))
            return
        for head, step in near.get(here, []):
            if head not in seen:
                seen.append(head)
                walk(head, seen, cost + step)
                seen.pop()

    walk(start, [start], 0)
    return found


def test_every_case_has_a_map() -> None:
    assert set(MAPS) == set(Case)


@pytest.mark.parametrize("case", list(Case))
def test_each_map_is_a_map(case: Case) -> None:
    start, goal, _ = MAPS[case]
    assert links_problem(edges(case), "the map") is None
    assert start != goal
    assert {start, goal} <= set(nodes_of(case))


@pytest.mark.parametrize("case", list(Case))
def test_the_verifier_and_the_plugin_find_the_same_cheapest_cost(case: Case) -> None:
    # The verifier may not import the plugin, so it searches the map again on purpose.
    start, goal, _ = MAPS[case]
    _, cost = cheapest(case)
    assert lowest_cost(edges(case), start, goal) == cost


@pytest.mark.parametrize("case", list(Case))
def test_exhaustive_search_agrees_with_both(case: Case) -> None:
    # A third search, independent of either Dijkstra: small maps make this affordable.
    _, cost = cheapest(case)
    assert min(found for found, _ in every_route(case)) == cost


@pytest.mark.parametrize("case", list(Case))
def test_the_route_the_plugin_names_is_real_and_costs_what_it_says(case: Case) -> None:
    start, goal, _ = MAPS[case]
    route, cost = cheapest(case)
    assert route_problem(route, edges(case), start, goal, "the route") is None
    assert route_cost(route, edges(case)) == cost


def test_quarry_has_exactly_two_cheapest_routes() -> None:
    # Without a tie there is nothing forcing the check to judge cost rather than match an answer.
    best = min(cost for cost, _ in every_route(Case.QUARRY))
    ties = [route for cost, route in every_route(Case.QUARRY) if cost == best]
    assert sorted(ties) == [["A", "B", "D", "E"], ["A", "C", "D", "E"]]


@pytest.mark.parametrize("case", [Case.ORCHARD, Case.FOUNDRY, Case.HARBOUR])
def test_the_other_maps_have_one_cheapest_route(case: Case) -> None:
    best = min(cost for cost, _ in every_route(case))
    assert len([route for cost, route in every_route(case) if cost == best]) == 1


def test_foundrys_cheapest_first_step_leads_away_from_the_cheapest_route() -> None:
    start, _, links = MAPS[Case.FOUNDRY]
    out = [(other if one == start else one, cost) for one, other, cost in links if start in (one, other)]
    greedy, _ = min(out, key=lambda step: step[1])
    route, _ = cheapest(Case.FOUNDRY)
    assert route[1] != greedy


@pytest.mark.parametrize("case", list(Case))
def test_a_node_sees_every_link_that_touches_it(case: Case) -> None:
    for node in nodes_of(case):
        touching = links_touching(case, [node])
        assert touching == [link for link in MAPS[case][2] if node in (link[0], link[1])]
        assert touching, f"{node} is on the map but has no links"


@pytest.mark.parametrize("case", list(Case))
def test_asking_about_every_node_gives_the_whole_map(case: Case) -> None:
    assert links_touching(case, nodes_of(case)) == MAPS[case][2]


def test_a_node_that_is_not_on_the_map_raises() -> None:
    with pytest.raises(ValueError, match="no such node"):
        links_touching(Case.ORCHARD, ["Z"])
