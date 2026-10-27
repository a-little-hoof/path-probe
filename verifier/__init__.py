"""The deterministic verifier: each tool's checks live in its own module, on contract instances."""

from contract import Task, Tool

from . import looking, puzzle, route

TOOLS = {
    Tool.READ_MAP: puzzle,
    Tool.NEIGHBOURS: looking,
    Tool.BEST_ROUTE: route,
}

# task -> its output's check, verify_task(arguments, output, reference, workspace)
TASKS = {
    Task.FIND_ROUTE: route.verify_task,
}


def verify_input(tool, value):
    return TOOLS[Tool(tool)].verify_input(value)


def verify_output(tool, input_value, output_value, workspace):
    return TOOLS[Tool(tool)].verify_output(input_value, output_value, workspace)


def verify_task(task, arguments, output, reference, workspace):
    return TASKS[Task(task)](arguments, output, reference, workspace)
