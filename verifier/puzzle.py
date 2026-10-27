"""read_map: what the model is told before it explores anything."""

from .checks import result


def verify_input(value):
    # case is an Enum member, so the only wrong value is one the type already refuses.
    return result(True, f"{value.case.value} is a case")


def verify_output(input_value, output_value, workspace):
    if output_value.case is not input_value.case:
        return result(False, f"the map is {output_value.case.value}, not {input_value.case.value}")
    if not output_value.start or not output_value.goal:
        return result(False, "the map must name both a start and a goal")
    if output_value.start == output_value.goal:
        return result(False, f"the start and the goal are both {output_value.start}, so there is nothing to find")
    if output_value.nodes < 2:
        return result(False, f"a map with {output_value.nodes} nodes cannot hold a route")
    return result(True, f"{output_value.start} to {output_value.goal} over {output_value.nodes} nodes")
