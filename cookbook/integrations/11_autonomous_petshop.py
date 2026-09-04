# /// script
# requires-python = ">=3.11"
# dependencies = ["langgraph>=0.2", "pyyaml>=6.0"]
# ///
"""The Autonomous Petshop — graph engineering with LangGraph.

The app: given a multi-API system that needs cross-API correlation (the real
Swagger Petstore + our weather fixture), comprehend every operation, find the
joins between them, emit an **Arazzo** workflow spec, run a **dynamic
simulation** of that workflow, and assemble a **consumable agent graph** —
the artifact that lets agents route intents and cross values between calls.

This is the cookbook miniature of what Gecko does at production quality
(value-domain signatures, provenance ladders, overlays measured by
execution). The output graph mirrors the shape of
cookbook/fixtures/program-graph-example.json, and the pipeline itself is a
LangGraph StateGraph — the concept demonstrated by the tool demonstrating it.

Note what is absent: there is NO model call anywhere in this file. Graph
engineering is the deterministic scaffolding around the model; the agent
consumes the graph this produces.

Run (uv resolves langgraph + pyyaml ephemerally from the header above):

    uv run cookbook/integrations/11_autonomous_petshop.py            # offline, fixtures
    PETSTORE_LIVE=1 uv run cookbook/integrations/11_autonomous_petshop.py
        # fetches https://petstore.swagger.io/v2/swagger.json and executes the
        # workflow's GET steps against the real demo API. Write steps (POST)
        # stay simulated even live — a real system demands a receipt-style
        # check before any call that counts. That rule is the course thesis.

Outputs (gitignored): petshop_out/adopt-a-pet.arazzo.yaml, petshop_out/agent_graph.json
"""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, TypedDict

import yaml
from langgraph.graph import END, StateGraph

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parent / "fixtures"
OUT_DIR = HERE / "petshop_out"
PETSTORE_SPEC_URL = "https://petstore.swagger.io/v2/swagger.json"
LIVE = os.environ.get("PETSTORE_LIVE") == "1"


# --------------------------------------------------------------------------- model
@dataclass(frozen=True)
class Operation:
    source: str  # which API this belongs to
    op_id: str
    method: str
    path: str
    params: tuple[tuple[str, str], ...]  # (name, location: path|query|body)
    output_schema: str  # schema name of the 200 response ("" if unknown)
    output_is_list: bool
    base_url: str


@dataclass(frozen=True)
class Join:
    from_op: str
    output_field: str  # e.g. "Pet.id"
    to_op: str
    input_param: str  # e.g. "petId"
    provenance: str  # "declared" (structural) | "inferred" (name match)


class PetshopState(TypedDict, total=False):
    operations: list[Operation]
    schemas: dict[str, dict[str, Any]]  # schema name -> {property: type}
    joins: list[Join]
    refusals: list[str]
    arazzo: dict[str, Any]
    trace: list[str]
    outputs_written: list[str]


# ----------------------------------------------------------------- spec loading
def _load_specs() -> dict[str, tuple[dict, str]]:
    """Return {api_name: (parsed_spec, base_url)} — live petstore when opted in."""
    specs: dict[str, tuple[dict, str]] = {}
    if LIVE:
        with urllib.request.urlopen(PETSTORE_SPEC_URL, timeout=20) as response:
            spec = json.loads(response.read())
        specs["petstore"] = (spec, "https://petstore.swagger.io/v2")
    else:
        spec = yaml.safe_load((FIXTURES / "petstore-mini.yaml").read_text())
        specs["petstore"] = (spec, spec["servers"][0]["url"])
    weather = yaml.safe_load((FIXTURES / "weather-mini.yaml").read_text())
    specs["weather"] = (weather, weather["servers"][0]["url"])
    return specs


def _schema_name(node: dict) -> tuple[str, bool]:
    """Resolve a response/body schema node to (schema name, is_list)."""
    if not isinstance(node, dict):
        return "", False
    if "$ref" in node:
        return node["$ref"].rsplit("/", 1)[-1], False
    if node.get("type") == "array":
        name, _ = _schema_name(node.get("items", {}))
        return name, True
    return "", False


def comprehend(state: PetshopState) -> PetshopState:
    """Node 1 — every operation of every API, normalized (OpenAPI v2 and v3)."""
    operations: list[Operation] = []
    schemas: dict[str, dict[str, Any]] = {}
    for api_name, (spec, base_url) in _load_specs().items():
        raw_schemas = spec.get("definitions") or spec.get("components", {}).get("schemas", {})
        for name, schema in raw_schemas.items():
            schemas[name] = {
                prop: sub.get("type", "object")
                for prop, sub in schema.get("properties", {}).items()
            }
        for path, methods in spec.get("paths", {}).items():
            for method, op in methods.items():
                if method not in ("get", "post", "put", "delete"):
                    continue
                params: list[tuple[str, str]] = []
                body_schema = ""
                for param in op.get("parameters", []):
                    if param.get("in") == "body":  # v2 style
                        body_schema, _ = _schema_name(param.get("schema", {}))
                    else:
                        params.append((param["name"], param.get("in", "query")))
                if "requestBody" in op:  # v3 style
                    content = op["requestBody"].get("content", {})
                    for media in content.values():
                        body_schema, _ = _schema_name(media.get("schema", {}))
                        break
                if body_schema and body_schema in schemas:
                    params.extend((prop, "body") for prop in schemas[body_schema])
                ok = op.get("responses", {}).get("200", {})
                out_node = ok.get("schema") or ok.get("content", {}).get(
                    "application/json", {}
                ).get("schema", {})
                out_name, is_list = _schema_name(out_node or {})
                operations.append(
                    Operation(
                        source=api_name,
                        op_id=op.get("operationId", f"{method}_{path}"),
                        method=method.upper(),
                        path=path,
                        params=tuple(params),
                        output_schema=out_name,
                        output_is_list=is_list,
                        base_url=base_url,
                    )
                )
    return {"operations": operations, "schemas": schemas}


# ----------------------------------------------------------------- correlation
def correlate(state: PetshopState) -> PetshopState:
    """Node 2 — cross-operation joins by value domain.

    Two honesty tiers, and the difference matters:
    - "declared": structural — a path parameter on a path whose GET returns
      schema S (the spec itself ties {sId} to S.id).
    - "inferred": a name match only (Order.petId looks like Pet.id). Real
      cross-API joins need a value-domain SIGNATURE, not a name; names are
      where fabricated edges come from, so these are labeled, not hidden.
    """
    operations = state["operations"]
    schemas = state["schemas"]
    joins: list[Join] = []
    refusals: list[str] = []

    def id_param_schema(param_name: str) -> str | None:
        """petId -> Pet, orderId -> Order — when that schema exists with an id."""
        if not param_name.endswith("Id"):
            return None
        stem = param_name[:-2]
        for name in schemas:
            if name.lower() == stem.lower() and "id" in schemas[name]:
                return name
        return None

    producers: dict[str, list[Operation]] = {}
    for op in operations:
        if op.output_schema and "id" in schemas.get(op.output_schema, {}):
            producers.setdefault(op.output_schema, []).append(op)

    for op in operations:
        for param_name, location in op.params:
            schema = id_param_schema(param_name)
            if schema is None:
                continue
            provenance = "declared" if location == "path" else "inferred"
            for producer in producers.get(schema, []):
                if producer.op_id == op.op_id or producer.source != op.source:
                    continue  # same-op loops out; cross-API needs more than a name
                joins.append(
                    Join(
                        from_op=producer.op_id,
                        output_field=f"{schema}.id",
                        to_op=op.op_id,
                        input_param=param_name,
                        provenance=provenance,
                    )
                )

    apis = {op.source for op in operations}
    if len(apis) > 1:
        cross = [j for j in joins if _source(operations, j.from_op) != _source(operations, j.to_op)]
        if not cross:
            refusals.append(
                "no declared join between "
                + " and ".join(sorted(apis))
                + " — the value domains do not overlap, so the graph refuses to "
                "invent a cross-API edge. An agent consuming this graph will not "
                "hallucinate one either; that refusal is the point."
            )
    return {"joins": joins, "refusals": refusals}


def _source(operations: list[Operation], op_id: str) -> str:
    return next(op.source for op in operations if op.op_id == op_id)


def _by_id(operations: list[Operation], op_id: str) -> Operation:
    return next(op for op in operations if op.op_id == op_id)


# ----------------------------------------------------------------- arazzo emission
def emit_arazzo(state: PetshopState) -> PetshopState:
    """Node 3 — the workflow is a PATH through the correlation graph.

    Start at the operation that lists pets, then follow join edges (a bounded
    walk, max 4 steps) binding each step's output to the next step's input.
    Arazzo's own answer to "a list came back" is index-0 binding
    ($response.body#/0/id) — exactly the arity limitation our fuller Arazzo
    work refuses; here it is used and labeled.
    """
    operations = state["operations"]
    joins = state["joins"]
    candidates = [op for op in operations if op.output_schema == "Pet" and op.output_is_list]
    # The real petstore has two list operations; findByStatus is the one whose
    # query we can honestly answer ("available"), so it wins the tie.
    start = sorted(candidates, key=lambda op: "findByStatus" not in op.op_id)[0]
    steps: list[dict[str, Any]] = []
    visited = {start.op_id}
    current = start
    binding = "$response.body#/0/id"  # index-0: the Arazzo-spec answer to lists
    steps.append(
        {
            "stepId": f"step-{current.op_id}",
            "operationId": current.op_id,
            "successCriteria": [{"condition": "$statusCode == 200"}],
            "outputs": {"petId": binding},
        }
    )
    for _ in range(3):  # bounded walk — a loop with no budget is a bug
        candidates = [j for j in joins if j.from_op == current.op_id and j.to_op not in visited]
        if not candidates:
            break
        # Prefer reads before writes, and order-shaped operations over side
        # quests (uploadFile, deletePet) — the intent is "adopt a pet".
        edge = min(
            candidates,
            key=lambda j: (
                _by_id(operations, j.to_op).method != "GET",
                "order" not in j.to_op.lower(),
            ),
        )
        nxt = _by_id(operations, edge.to_op)
        visited.add(nxt.op_id)
        prev_step = steps[-1]["stepId"]
        out_key = edge.input_param
        step: dict[str, Any] = {
            "stepId": f"step-{nxt.op_id}",
            "operationId": nxt.op_id,
            "successCriteria": [{"condition": "$statusCode == 200"}],
        }
        value = f"$steps.{prev_step}.outputs.{out_key}"
        locations = dict(nxt.params)
        if locations.get(edge.input_param) == "body":
            step["requestBody"] = {
                "contentType": "application/json",
                "payload": {edge.input_param: value, "quantity": 1},
            }
        else:
            step["parameters"] = [
                {
                    "name": edge.input_param,
                    "in": locations.get(edge.input_param, "path"),
                    "value": value,
                }
            ]
        if nxt.output_schema and "id" in state["schemas"].get(nxt.output_schema, {}):
            step["outputs"] = {
                f"{nxt.output_schema.lower()}Id": "$response.body#/id",
            }
        steps.append(step)
        current = nxt

    arazzo = {
        "arazzo": "1.0.1",
        "info": {
            "title": "Autonomous Petshop — adopt a pet",
            "version": "1.0.0",
            "description": "Generated by walking the correlation graph; each "
            "step binding is a join edge with a provenance label in agent_graph.json.",
        },
        "sourceDescriptions": [
            {"name": "petstore", "url": PETSTORE_SPEC_URL, "type": "openapi"},
            {"name": "weather", "url": "./fixtures/weather-mini.yaml", "type": "openapi"},
        ],
        "workflows": [
            {
                "workflowId": "adopt-a-pet",
                "summary": "Find an available pet, inspect it, order it, confirm the order.",
                "steps": steps,
            }
        ],
    }
    return {"arazzo": arazzo}


# ----------------------------------------------------------------- simulation
def _sample(schema_name: str, schemas: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Deterministic example from a schema — recorded mode's whole trick."""
    kinds = schemas.get(schema_name, {})
    sample: dict[str, Any] = {}
    for prop, kind in kinds.items():
        sample[prop] = {"integer": 1, "number": 1.0, "boolean": True}.get(kind, "example")
    return sample


def simulate(state: PetshopState) -> PetshopState:
    """Node 4 — execute the workflow: recorded by default, live GETs opt-in.

    One code path; the transport edge decides. Write steps (POST/PUT/DELETE)
    are NEVER sent live from this script — a call that changes state deserves
    a receipt-style verification first, and this cookbook does not carry one.
    """
    operations = state["operations"]
    schemas = state["schemas"]
    trace: list[str] = []
    step_outputs: dict[str, dict[str, Any]] = {}

    for step in state["arazzo"]["workflows"][0]["steps"]:
        op = _by_id(operations, step["operationId"])
        # Resolve bindings from earlier steps.
        bound: dict[str, Any] = {}
        for param in step.get("parameters", []):
            value = param["value"]
            if isinstance(value, str) and value.startswith("$steps."):
                _, step_id, _, key = value.split(".", 3)
                bound[param["name"]] = step_outputs[step_id][key]
            else:
                bound[param["name"]] = value
        mode = "recorded"
        body: Any = None
        if LIVE and op.method == "GET" and "petstore.swagger.io" in op.base_url:
            path = op.path
            for name, value in bound.items():
                path = path.replace("{" + name + "}", str(value))
            query = "?status=available" if "findByStatus" in op.op_id else ""
            url = f"{op.base_url}{path}{query}"
            try:
                with urllib.request.urlopen(url, timeout=20) as response:
                    body = json.loads(response.read())
                if body == [] or body is None:  # a demo API with no data is a flake, not a fact
                    trace.append("    (live call returned nothing; falling back to recorded)")
                    body = None
                else:
                    mode = "live"
            except Exception as error:  # noqa: BLE001 — a live demo API flakes; recorded absorbs it
                trace.append(f"    (live call failed: {type(error).__name__}; falling back)")
        if body is None:
            body = _sample(op.output_schema, schemas)
            if op.output_is_list:
                body = [body]
        if op.method != "GET":
            mode = "recorded (write steps never go live from this script)"

        outputs: dict[str, Any] = {}
        for key in step.get("outputs", {}):
            record = body[0] if isinstance(body, list) else body
            outputs[key] = record.get("id", 1) if isinstance(record, dict) else 1
        step_outputs[step["stepId"]] = outputs
        bound_note = f" with {bound}" if bound else ""
        trace.append(f"[{mode}] {op.method} {op.path}{bound_note} -> outputs {outputs or '{}'}")
    return {"trace": trace}


# ----------------------------------------------------------------- agent graph
def assemble_graph(state: PetshopState) -> PetshopState:
    """Node 5 — the consumable artifact: nodes, provenance-labeled edges, intents."""
    OUT_DIR.mkdir(exist_ok=True)
    graph = {
        "_comment": "Consumable agent graph — same shape as "
        "cookbook/fixtures/program-graph-example.json. Edges carry provenance; "
        "'inferred' edges are usable but must be verified before anything counts.",
        "apis": sorted({op.source for op in state["operations"]}),
        "nodes": [
            {
                "op": op.op_id,
                "api": op.source,
                "call": f"{op.method} {op.path}",
                "returns": (op.output_schema or "unknown") + ("[]" if op.output_is_list else ""),
            }
            for op in state["operations"]
        ],
        "edges": [asdict(join) for join in state["joins"]],
        "refusals": state["refusals"],
        "intents": [
            {
                "intent": "adopt a pet / buy a pet",
                "start": state["arazzo"]["workflows"][0]["steps"][0]["operationId"],
            },
        ],
        "workflow_spec": "adopt-a-pet.arazzo.yaml",
    }
    arazzo_path = OUT_DIR / "adopt-a-pet.arazzo.yaml"
    graph_path = OUT_DIR / "agent_graph.json"
    arazzo_path.write_text(yaml.safe_dump(state["arazzo"], sort_keys=False), encoding="utf-8")
    graph_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    return {"outputs_written": [str(arazzo_path), str(graph_path)]}


# ----------------------------------------------------------------- the graph of graphs
def build_pipeline() -> Any:
    """The pipeline itself is a LangGraph StateGraph — drawn, then executed."""
    builder = StateGraph(PetshopState)
    builder.add_node("comprehend", comprehend)
    builder.add_node("correlate", correlate)
    builder.add_node("emit_arazzo", emit_arazzo)
    builder.add_node("simulate", simulate)
    builder.add_node("assemble_graph", assemble_graph)
    builder.set_entry_point("comprehend")
    builder.add_edge("comprehend", "correlate")
    # A conditional edge: no joins would mean no workflow to emit — the graph
    # ends with the refusal recorded instead of fabricating a path.
    builder.add_conditional_edges(
        "correlate",
        lambda state: "emit_arazzo" if state["joins"] else END,
        {"emit_arazzo": "emit_arazzo", END: END},
    )
    builder.add_edge("emit_arazzo", "simulate")
    builder.add_edge("simulate", "assemble_graph")
    builder.add_edge("assemble_graph", END)
    return builder.compile()


def main() -> int:
    pipeline = build_pipeline()
    # The pipeline drawn as mermaid — paste it anywhere that renders mermaid
    # (GitHub, the course guides) to SEE the graph you are about to execute.
    print(pipeline.get_graph().draw_mermaid())
    print(f"mode: {'LIVE petstore (GET steps only)' if LIVE else 'recorded (fixtures)'}\n")

    state = pipeline.invoke({})

    print(
        f"operations comprehended: {len(state['operations'])} "
        f"across {sorted({op.source for op in state['operations']})}"
    )
    print("\njoins (the correlation graph):")
    for join in state["joins"]:
        print(
            f"  {join.from_op}:{join.output_field} -> {join.to_op}({join.input_param})"
            f"  [{join.provenance}]"
        )
    for refusal in state["refusals"]:
        print(f"\nrefusal: {refusal}")
    print("\nworkflow simulation:")
    for line in state.get("trace", []):
        print(f"  {line}")
    print()
    for path in state.get("outputs_written", []):
        print(f"written: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
