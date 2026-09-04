<!-- title: Agent Loops -->
<!-- tags: agent, loop, tools, budget, autonomy -->

# Agent Loops

An agent is a loop: the model observes some state, decides on an action, the
application executes that action, and the result feeds the next observation. What
separates a reliable agent from an expensive random walk is not the model — it is
the engineering of the loop around it.

## The anatomy of one iteration

Each pass through the loop has four parts. **Perceive**: assemble the context the
model will see — the question, retrieved documents, previous tool results.
**Decide**: the model chooses to answer directly or to call a tool. **Act**: the
application validates the chosen tool's arguments and executes it. **Observe**: the
tool result is appended to the context. The application owns three of these four
steps; only the decision belongs to the model.

## Budgets and stopping conditions

An unbounded loop is a bug, not a feature. Every production loop carries a budget:
a maximum number of tool calls, a token ceiling, or a wall-clock timeout. When the
budget is exhausted, the loop must stop in a defined state — typically a refusal
with an explanation — rather than truncating silently. Stopping conditions worth
implementing from day one: the model produced a final answer, the budget ran out,
a tool failed unrecoverably, or the same tool was called with the same arguments
twice (a loop-detection guard).

## Choose the least autonomy that works

There is a spectrum: a deterministic chain (no decisions), a tool-using loop (the
model picks tools), a reflection loop (the model critiques its own draft), and
multi-agent systems (models delegate to models). Each step up adds latency, cost,
and failure modes. The professional habit is to start at the bottom of the
spectrum and move up only when a measured failure justifies it. A workflow that
can be a fixed pipeline should be a fixed pipeline.

## Refusal is a first-class outcome

A loop that cannot refuse will fabricate. When retrieval returns nothing relevant,
the correct behavior is to say so — before spending a model call — and flag the
answer for human review. Design the refusal path first; it is the path every other
safeguard falls back to.
