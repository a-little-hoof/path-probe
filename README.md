# Path Probe

Each case is a small weighted map that is never shown whole. The task is to
explore it a node at a time and come back with the cheapest route from its
start to its goal. The plugin is a standard MCP server over stdio; NanoAgent
owns its launch command, environment, input and output checks and lifecycle.

## Tools

| Tool | Does | Code |
|---|---|---|
| `read_map` | Returns where a route must start and end, and how many nodes the map holds, so the agent knows when it has seen them all | `src/plugin/routes.py` |
| `neighbours` | Returns every link touching the nodes asked about, and nothing else. Several nodes can be asked about in one call | `src/plugin/routes.py` |
| `best_route` | Returns the map's whole link list and its cheapest route. It is `find-route`'s reference tool, so no task lists it and the model never sees its output | `src/plugin/routes.py` |

### Tasks

| Task | Does | Runner |
|---|---|---|
| `find-route` | Explores a map and finds the cheapest route from its start to its goal | `agent`, with `read_map` and `neighbours`, against the `best_route` reference |

The four maps (`orchard`, `quarry`, `foundry`, `harbour`) are six to eight
nodes each. They are small on purpose: a handful of `neighbours` calls maps one
out, so the task is exploring under partial sight rather than outlasting a long
loop. Links are undirected and every cost is above zero, so a cheapest route
never visits a node twice.

Each map has a character the check needs:

- `orchard` has one cheapest route.
- `quarry` has **two** equally cheap routes, so the check cannot work by
  comparing against one stored answer.
- `foundry`'s cheapest first step leads away from its cheapest route, so a
  greedy walk produces something real and wrong.
- `harbour` is the largest, and its cheapest route runs through all eight
  nodes, so route length proves nothing by itself.

## What makes it checkable

Finding a cheapest route follows from the map, so if the model could see the
map there would be no task. What it actually has to do is decide where to look
next on partial information, and then produce a route. The check does not ask
whether the route is the reference's; it asks two things code can settle:

1. Is the route real? Every consecutive pair must be a link on the map, with no
   node visited twice, starting at the start and ending at the goal.
2. Is it cheapest? Its cost must equal what the map allows, which the verifier
   works out by searching the map itself.

Any cheapest route passes, which is why `quarry` exists. A route that is real
but dearer is scored by how close it comes — the cheapest cost over the cost
submitted — so the greedy walk on `foundry` scores 0.9 rather than 0.

## Layout

It has the standard plugin layout, which NanoAgent requires:

```text
.
├── nanoagent.yaml   # manifest (a slimconfig ManifestConfig): id, runtime, permissions, tools, tasks
├── contract.py      # each tool's and task's typed input and output: slimconfig Output classes
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .env             # needed environment variable names (none here)
├── src/plugin/      # the MCP server (__main__.py, its IMPLEMENTATIONS table), maps.py and the tools
├── tests/           # test_verifier.py and test_maps.py, the design's invariants
├── ui/              # how the page draws the outputs: renderers.js and renderers.css
├── product/         # the product page a catalog shows: product.yaml and icon.svg
└── verifier/        # deterministic verifier package: checks.py, puzzle.py, looking.py and route.py
```

`contract.py` types every value: the server builds each call's input into its
class and checks its output against its own, and NanoAgent and the verifier
get the same classes. A failing tool raises, and the MCP server returns an
error result.

`verifier/` is deterministic and imports nothing but `contract` and its own
package. Because it may not import the plugin, it writes its own shortest-route
search and uses it on the link list the reference hands it: it takes no tool's
word for what the cheapest route costs, including the reference tool's, whose
route and cost it checks against the map before using them.
`tests/test_maps.py` holds the two searches in step and checks both against a
third, exhaustive one — the maps are small enough to enumerate every route.

## Develop and run

```bash
uv sync --extra dev
uv run pytest
```

NanoAgent passes the folder the plugin may write to as `NANOAGENT_WORKSPACE`.
No tool writes to it: every map is held in `src/plugin/maps.py`, so a run needs
no network and no files.
