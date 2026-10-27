"""Each tool's and task's typed input and output (see nanoagent.plugin.v0001.contract): declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    READ_MAP = "read_map"
    NEIGHBOURS = "neighbours"
    BEST_ROUTE = "best_route"


class Task(Enum):
    FIND_ROUTE = "find-route"


class Case(Enum):
    ORCHARD = "orchard"
    QUARRY = "quarry"
    FOUNDRY = "foundry"
    HARBOUR = "harbour"


CASE = "Which map to work on; the map is never shown whole, only a node at a time"
START = "The node a route starts at"
GOAL = "The node a route must reach"
ROUTE = "The nodes travelled in order, the start first and the goal last, each one named once"
COST = "What the whole route costs: the costs of the links it travels, added up"


@dataclass
class Link(Output):
    start: Annotated[str, "One end of the link"]
    end: Annotated[str, "The other end; links can be travelled either way"]
    cost: Annotated[int, "What travelling this link costs, always more than zero"]


@dataclass
class CaseInput(Output):
    case: Annotated[Case, CASE]


@dataclass
class MapOutput(Output):
    case: Annotated[Case, "The map this describes"]
    start: Annotated[str, START]
    goal: Annotated[str, GOAL]
    nodes: Annotated[int, "How many nodes the map holds in all, so you know when you have seen them"]


@dataclass
class NeighboursInput(Output):
    case: Annotated[Case, CASE]
    nodes: Annotated[list[str], "The nodes to look at, one or more; ask about several at once"]


@dataclass
class NeighboursOutput(Output):
    case: Annotated[Case, "The map this comes from"]
    links: Annotated[list[Link], "Every link touching the nodes asked about, each one named once"]


@dataclass
class RouteOutput(Output):
    case: Annotated[Case, "The map the route crosses, as the task gave it"]
    route: Annotated[list[str], ROUTE]
    cost: Annotated[int, COST]


@dataclass
class BestRouteOutput(Output):
    case: Annotated[Case, "The map the route crosses"]
    start: Annotated[str, START]
    goal: Annotated[str, GOAL]
    links: Annotated[list[Link], "Every link on the map, each one named once"]
    route: Annotated[list[str], ROUTE]
    cost: Annotated[int, "The lowest cost any route from the start to the goal can have"]


TOOLS = {
    Tool.READ_MAP: (CaseInput, MapOutput),
    Tool.NEIGHBOURS: (NeighboursInput, NeighboursOutput),
    Tool.BEST_ROUTE: (CaseInput, BestRouteOutput),
}
TASKS = {
    Task.FIND_ROUTE: (CaseInput, RouteOutput),
}
