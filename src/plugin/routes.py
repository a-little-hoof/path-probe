"""read_map, neighbours and best_route: the puzzle, one look at it, and its answer."""

from __future__ import annotations

from pathlib import Path

from contract import BestRouteOutput, CaseInput, Link, MapOutput, NeighboursInput, NeighboursOutput
from plugin.maps import MAPS, cheapest, links_touching, nodes_of


def _links(raw: list[tuple[str, str, int]]) -> list[Link]:
    return [Link(start=one, end=other, cost=cost) for one, other, cost in raw]


def read_map(given: CaseInput, workspace: Path) -> MapOutput:
    start, goal, _ = MAPS[given.case]
    return MapOutput(case=given.case, start=start, goal=goal, nodes=len(nodes_of(given.case)))


def neighbours(given: NeighboursInput, workspace: Path) -> NeighboursOutput:
    asked = [node.strip().upper() for node in given.nodes]
    if not asked or any(not node for node in asked):
        raise ValueError("ask about at least one node, and name each one")
    return NeighboursOutput(case=given.case, links=_links(links_touching(given.case, asked)))


def best_route(given: CaseInput, workspace: Path) -> BestRouteOutput:
    """The task's reference tool: NanoAgent runs it out of the model's sight."""
    start, goal, links = MAPS[given.case]
    route, cost = cheapest(given.case)
    return BestRouteOutput(
        case=given.case,
        start=start,
        goal=goal,
        links=_links(links),
        route=route,
        cost=cost,
    )
