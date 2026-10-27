"""neighbours: one look at the map, which may only report links it was asked about."""

from .checks import links_problem, result


def verify_input(value):
    asked = [node.strip().upper() for node in value.nodes]
    if not asked:
        return result(False, "ask about at least one node")
    if any(not node for node in asked):
        return result(False, "every node asked about must be named")
    if len(set(asked)) != len(asked):
        return result(False, "do not ask about the same node twice")
    return result(True, f"looking at {len(asked)} node(s)")


def verify_output(input_value, output_value, workspace):
    if output_value.case is not input_value.case:
        return result(False, f"the links are from {output_value.case.value}, not {input_value.case.value}")
    problem = links_problem(output_value.links, "the links")
    if problem:
        return result(False, problem)
    asked = {node.strip().upper() for node in input_value.nodes}
    stray = [
        f"{link.start}-{link.end}" for link in output_value.links if link.start not in asked and link.end not in asked
    ]
    if stray:
        return result(False, f"links {stray} touch no node that was asked about")
    return result(True, f"{len(output_value.links)} link(s) touch the nodes asked about")
