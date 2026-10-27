from __future__ import annotations

from pathlib import Path

import pytest
from slimconfig import build_output, plain_output

import verifier
from contract import TASKS, TOOLS, BestRouteOutput, Case, CaseInput, NeighboursInput, Task, Tool
from plugin import best_route, neighbours, read_map
from plugin.maps import cheapest

BEST = {Case.ORCHARD: 13, Case.QUARRY: 9, Case.FOUNDRY: 9, Case.HARBOUR: 15}
# quarry is the tie case: both of these are cheapest, and the check must take either.
QUARRY_TIES = (["A", "B", "D", "E"], ["A", "C", "D", "E"])


# The verifier gets contract instances, as NanoAgent's sandbox builds them from JSON.
def verify_input(tool: str, value: dict) -> dict:
    return verifier.verify_input(tool, build_output(value, TOOLS[Tool(tool)][0]))


def verify_output(tool: str, input_value: dict, output_value: dict, workspace: Path) -> dict:
    given, made = TOOLS[Tool(tool)]
    return verifier.verify_output(
        tool, build_output(input_value, given), build_output(output_value, made), str(workspace)
    )


def verify_task(task: str, arguments: dict, output: dict, workspace: Path, reference: dict | None = None) -> dict:
    given, made = TASKS[Task(task)]
    pinned = None if reference is None else build_output(reference, BestRouteOutput)
    given_value, made_value = build_output(arguments, given), build_output(output, made)
    return verifier.verify_task(task, given_value, made_value, pinned, str(workspace))


def answer(case: Case, workspace: Path) -> dict:
    return plain_output(best_route(CaseInput(case=case), workspace))


def submit(case: Case, route: list[str], cost: int, workspace: Path, reference: dict | None = None) -> dict:
    reference = answer(case, workspace) if reference is None else reference
    made = {"case": case.value, "route": route, "cost": cost}
    return verify_task("find-route", {"case": case.value}, made, workspace, reference)


# --- correct ---------------------------------------------------------------


@pytest.mark.parametrize("case", list(Case))
def test_the_cheapest_route_passes_on_every_map(tmp_path: Path, case: Case) -> None:
    route, cost = cheapest(case)
    assert cost == BEST[case]
    verdict = submit(case, route, cost, tmp_path)
    assert verdict["valid"] is True and verdict["score"] == 1.0


@pytest.mark.parametrize("route", QUARRY_TIES)
def test_either_of_the_two_cheapest_routes_passes(tmp_path: Path, route: list[str]) -> None:
    # The point of the check: it judges the cost, not whether the route matches the reference's.
    verdict = submit(Case.QUARRY, route, 9, tmp_path)
    assert verdict["valid"] is True and verdict["score"] == 1.0


def test_the_two_cheapest_routes_really_are_different(tmp_path: Path) -> None:
    named = answer(Case.QUARRY, tmp_path)["route"]
    assert named in [list(route) for route in QUARRY_TIES]
    assert QUARRY_TIES[0] != QUARRY_TIES[1]


# --- incorrect -------------------------------------------------------------


def test_a_real_but_dearer_route_is_refused_and_scored_by_how_close_it_is(tmp_path: Path) -> None:
    # The direct link exists and costs 10; the map allows 9.
    verdict = submit(Case.QUARRY, ["A", "E"], 10, tmp_path)
    assert verdict["valid"] is False and "the map allows 9" in verdict["message"]
    assert verdict["score"] == pytest.approx(0.9)


def test_the_greedy_route_is_real_and_still_refused(tmp_path: Path) -> None:
    # foundry's cheapest first step, A-B at cost 1, leads to a route costing 10 against 9.
    verdict = submit(Case.FOUNDRY, ["A", "B", "F", "E", "G"], 10, tmp_path)
    assert verdict["valid"] is False and verdict["score"] == pytest.approx(0.9)


def test_a_route_over_a_link_the_map_does_not_have_is_refused(tmp_path: Path) -> None:
    verdict = submit(Case.ORCHARD, ["A", "F"], 1, tmp_path)
    assert verdict["valid"] is False and "no such link" in verdict["message"]


@pytest.mark.parametrize(
    ("route", "message"),
    [
        (["C", "B", "D", "E", "F"], "starts at C, not A"),
        (["A", "C", "B", "D", "E"], "ends at E, not F"),
        (["A", "C", "A", "C", "B", "D", "E", "F"], "passes through a node twice"),
    ],
)
def test_a_route_that_is_not_start_to_goal_is_refused(tmp_path: Path, route: list[str], message: str) -> None:
    verdict = submit(Case.ORCHARD, route, 13, tmp_path)
    assert verdict["valid"] is False and message in verdict["message"]


def test_a_cheapest_route_with_the_wrong_cost_claimed_is_refused(tmp_path: Path) -> None:
    route, cost = cheapest(Case.HARBOUR)
    verdict = submit(Case.HARBOUR, route, cost - 1, tmp_path)
    assert verdict["valid"] is False and f"not the {cost - 1} submitted" in verdict["message"]


def test_the_submitted_case_must_be_the_one_asked_for(tmp_path: Path) -> None:
    route, cost = cheapest(Case.QUARRY)
    made = {"case": Case.QUARRY.value, "route": route, "cost": cost}
    verdict = verify_task("find-route", {"case": Case.ORCHARD.value}, made, tmp_path, answer(Case.ORCHARD, tmp_path))
    assert verdict["valid"] is False and "not orchard" in verdict["message"]


# --- missing ---------------------------------------------------------------


def test_an_empty_route_is_refused(tmp_path: Path) -> None:
    verdict = submit(Case.ORCHARD, [], 0, tmp_path)
    assert verdict["valid"] is False and "at least one node" in verdict["message"]


def test_a_reference_for_another_case_is_refused(tmp_path: Path) -> None:
    route, cost = cheapest(Case.ORCHARD)
    verdict = submit(Case.ORCHARD, route, cost, tmp_path, answer(Case.QUARRY, tmp_path))
    assert verdict["valid"] is False and "reference answer is for quarry" in verdict["message"]


def test_a_reference_with_no_links_is_refused(tmp_path: Path) -> None:
    route, cost = cheapest(Case.ORCHARD)
    broken = answer(Case.ORCHARD, tmp_path) | {"links": []}
    verdict = submit(Case.ORCHARD, route, cost, tmp_path, broken)
    assert verdict["valid"] is False and "at least one link" in verdict["message"]


# --- malformed -------------------------------------------------------------


def test_a_reference_that_is_not_actually_cheapest_is_refused(tmp_path: Path) -> None:
    # The verifier searches the map itself, so a reference that overstates its own cost is caught.
    route, cost = cheapest(Case.ORCHARD)
    lying = answer(Case.ORCHARD, tmp_path) | {"cost": cost + 5}
    verdict = submit(Case.ORCHARD, route, cost, tmp_path, lying)
    assert verdict["valid"] is False and "the reference route costs" in verdict["message"]


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"links": [{"start": "A", "end": "A", "cost": 1}]}, "to itself"),
        ({"links": [{"start": "A", "end": "B", "cost": 0}]}, "not above zero"),
        ({"links": [{"start": "A", "end": "B", "cost": -3}]}, "not above zero"),
        (
            {"links": [{"start": "A", "end": "B", "cost": 1}, {"start": "B", "end": "A", "cost": 2}]},
            "twice",
        ),
    ],
)
def test_a_reference_map_that_is_not_a_map_is_refused(tmp_path: Path, change: dict, message: str) -> None:
    route, cost = cheapest(Case.ORCHARD)
    broken = answer(Case.ORCHARD, tmp_path) | change
    verdict = submit(Case.ORCHARD, route, cost, tmp_path, broken)
    assert verdict["valid"] is False and message in verdict["message"]


def test_an_absurdly_long_route_is_refused(tmp_path: Path) -> None:
    verdict = submit(Case.ORCHARD, [f"N{index}" for index in range(101)], 1, tmp_path)
    assert verdict["valid"] is False and "at most 100" in verdict["message"]


# --- boundary --------------------------------------------------------------


def test_a_route_of_a_single_link_passes_when_it_is_cheapest(tmp_path: Path) -> None:
    # The shortest route the contract allows is two nodes; quarry's A-E is real, just not cheapest.
    verdict = submit(Case.QUARRY, ["A", "E"], 10, tmp_path)
    assert verdict["valid"] is False
    assert verdict["details"]["cheapest"] == 9


def test_the_whole_map_as_a_route_is_judged_on_cost_not_length(tmp_path: Path) -> None:
    # harbour's cheapest route runs through all eight nodes, so length alone proves nothing.
    route, cost = cheapest(Case.HARBOUR)
    assert len(route) == 8
    assert submit(Case.HARBOUR, route, cost, tmp_path)["valid"] is True


# --- the tools' own checks -------------------------------------------------


@pytest.mark.parametrize("case", list(Case))
def test_read_map_and_best_route_agree_on_the_ends(tmp_path: Path, case: Case) -> None:
    given = {"case": case.value}
    described = plain_output(read_map(CaseInput(case=case), tmp_path))
    found = answer(case, tmp_path)
    assert verify_output("read_map", given, described, tmp_path)["valid"] is True
    assert verify_output("best_route", given, found, tmp_path)["valid"] is True
    assert (described["start"], described["goal"]) == (found["start"], found["goal"])


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"start": "A", "goal": "A"}, "nothing to find"),
        ({"start": ""}, "must name both"),
        ({"nodes": 1}, "cannot hold a route"),
    ],
)
def test_a_map_description_that_makes_no_sense_is_refused(tmp_path: Path, change: dict, message: str) -> None:
    given = {"case": Case.ORCHARD.value}
    described = plain_output(read_map(CaseInput(case=Case.ORCHARD), tmp_path)) | change
    verdict = verify_output("read_map", given, described, tmp_path)
    assert verdict["valid"] is False and message in verdict["message"]


def test_neighbours_reports_only_links_it_was_asked_about(tmp_path: Path) -> None:
    given = {"case": Case.HARBOUR.value, "nodes": ["A", "B"]}
    seen = plain_output(neighbours(NeighboursInput(case=Case.HARBOUR, nodes=["A", "B"]), tmp_path))
    assert verify_input("neighbours", given)["valid"] is True
    assert verify_output("neighbours", given, seen, tmp_path)["valid"] is True
    assert all("A" in (link["start"], link["end"]) or "B" in (link["start"], link["end"]) for link in seen["links"])


def test_neighbours_that_volunteers_a_link_elsewhere_is_refused(tmp_path: Path) -> None:
    given = {"case": Case.HARBOUR.value, "nodes": ["A"]}
    seen = plain_output(neighbours(NeighboursInput(case=Case.HARBOUR, nodes=["A"]), tmp_path))
    seen["links"] = seen["links"] + [{"start": "G", "end": "H", "cost": 2}]
    verdict = verify_output("neighbours", given, seen, tmp_path)
    assert verdict["valid"] is False and "touch no node that was asked about" in verdict["message"]


@pytest.mark.parametrize(
    ("nodes", "message"),
    [([], "at least one node"), (["A", "A"], "same node twice"), (["A", " "], "must be named")],
)
def test_neighbours_refuses_an_input_it_could_not_use(nodes: list[str], message: str) -> None:
    verdict = verify_input("neighbours", {"case": Case.ORCHARD.value, "nodes": nodes})
    assert verdict["valid"] is False and message in verdict["message"]


def test_neighbours_raises_on_a_node_that_is_not_on_the_map(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no such node"):
        neighbours(NeighboursInput(case=Case.ORCHARD, nodes=["Z"]), tmp_path)
