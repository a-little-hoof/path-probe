"""best_route (the find-route reference) and the find-route task's own check."""

from .checks import links_problem, lowest_cost, result, route_cost, route_problem


def verify_input(value):
    return result(True, f"{value.case.value} is a case")


def _answer_problem(value, label):
    """What is wrong with a map-and-cheapest-route answer, or None."""
    problem = links_problem(value.links, f"{label} map") or route_problem(
        value.route, value.links, value.start, value.goal, f"{label} route"
    )
    if problem:
        return problem
    walked = route_cost(value.route, value.links)
    if walked != value.cost:
        return f"{label} route costs {walked}, not the {value.cost} claimed"
    # The verifier searches the map itself rather than believing the answer is the cheapest.
    best = lowest_cost(value.links, value.start, value.goal)
    if best is None:
        return f"{label} map has no route from {value.start} to {value.goal}"
    if best != value.cost:
        return f"{label} route costs {value.cost}, but the map allows {best}"
    return None


def verify_output(input_value, output_value, workspace):
    if output_value.case is not input_value.case:
        return result(False, f"the answer is for {output_value.case.value}, not {input_value.case.value}")
    problem = _answer_problem(output_value, "the answer's")
    if problem:
        return result(False, problem)
    return result(True, f"{output_value.start} to {output_value.goal} costs {output_value.cost} at best")


def verify_task(arguments, output, reference, workspace):
    """find-route: the submitted route judged on whether it is real and whether it is cheapest.

    Any cheapest route passes, not only the one the reference happens to name: the maps include a
    case with two of them.
    """
    if output.case is not arguments.case:
        return result(False, f"the route is for {output.case.value}, not {arguments.case.value}")
    if reference.case is not arguments.case:
        return result(False, f"the reference answer is for {reference.case.value}, not {arguments.case.value}")
    # The verifier does not take the reference tool's word for it either.
    problem = _answer_problem(reference, "the reference")
    if problem:
        return result(False, problem)
    problem = route_problem(output.route, reference.links, reference.start, reference.goal, "the route")
    if problem:
        return result(False, problem)
    walked = route_cost(output.route, reference.links)
    if walked != output.cost:
        return result(False, f"the route costs {walked}, not the {output.cost} submitted")
    if walked > reference.cost:
        return result(
            False,
            f"the route is real but costs {walked}, and the map allows {reference.cost}",
            score=reference.cost / walked,
            cheapest=reference.cost,
        )
    return result(
        True,
        f"{' '.join(output.route)} costs {walked}, which is as cheap as the map allows",
        nodes=len(output.route),
    )
