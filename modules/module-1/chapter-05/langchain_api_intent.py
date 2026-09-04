"""LangChain template #2 — API operation -> semantic intent (optional pre-work).

The app: given the name of an API operation (e.g. "GET /pets/{petId}"),
generate a semantic description of its intent — what it does, what it
returns, when an agent should use it, and which operations it DEPENDS on
(before/after). The dependencies section is the graph-engineering hook: each
"call X first to obtain petId" line is an edge, and collecting those edges
across an API is exactly how a correlation graph gets built (see
cookbook/integrations/11_autonomous_petshop.py for the deterministic version).

Compare your output with cookbook/introduction/02_comprehend_an_openapi.ipynb,
which does the same job from a real spec — and notice what the full spec knows
that the bare operation name cannot.

Setup (optional material — not part of the course dependencies):
    uv add langchain langchain-openai
    export OPENAI_API_KEY=sk-...     # or put it in .env

Run:
    uv run python modules/module-1/chapter-05/langchain_api_intent.py
"""

from __future__ import annotations

import os
import sys

# Module-level so the Gradio app (langchain_api_intent_gradio.py) imports the
# same prompt — one source of truth, two surfaces.
PROMPT_TEXT = (
    "You are an API-comprehension layer for AI agents. Given an API operation, "
    "produce a semantic description of its intent, in four short sections:\n"
    "1. WHAT IT DOES — the action, in plain language, one sentence.\n"
    "2. WHAT IT RETURNS — the shape and meaning of the response, one sentence.\n"
    "3. WHEN AN AGENT SHOULD USE IT — the user intents that should route here, "
    "and one intent that should NOT (name the operation it should route to "
    "instead, if you can infer one).\n"
    "4. DEPENDENCIES — operations that typically must be called BEFORE this one "
    "(to obtain its inputs, e.g. where does the id in the path come from?) and "
    "operations typically called AFTER it (to consume its outputs). For each "
    "dependency, mark it [declared] when the operation shape itself implies it, "
    "or [guessed] when you are inferring from naming conventions.\n\n"
    "Be factual about what the operation name alone can tell you; if something is "
    "unknowable without the full spec (auth, error shapes, pagination), say so "
    "explicitly instead of guessing.\n\n"
    "API operation: {operation}"
)


def main() -> int:
    # Graceful skips first: optional material must never crash a fresh clone.
    try:
        # 1. Import the required LangChain components
        from langchain.chat_models import init_chat_model
        from langchain_core.prompts import PromptTemplate
    except ImportError:
        print("SKIP: LangChain is not installed (this is optional pre-work).")
        print("      To run it: uv add langchain langchain-openai")
        return 0

    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    if not os.environ.get("OPENAI_API_KEY"):
        print("SKIP: OPENAI_API_KEY is not set (this template makes a live call).")
        print("      Set it in .env, then rerun. Nothing else in the course needs it.")
        return 0

    # 2. Create a PromptTemplate with a variable for the API operation
    prompt_template = PromptTemplate.from_template(PROMPT_TEXT)

    # 3. Initialize the model (gpt-4o-mini, provider openai)
    model = init_chat_model("gpt-4o-mini", model_provider="openai")

    # 4. Format the prompt with an example operation, call the model, print response.text
    operation = "GET /pets/{petId}"
    prompt = prompt_template.format(operation=operation)
    response = model.invoke(prompt)
    print(response.text)

    # Follow-up exercises:
    # - Try "POST /orders" — does the model flag that auth is unknowable here?
    #   (The real spec in cookbook/fixtures/petstore-mini.yaml marks it as
    #   credentialed; the bare name cannot know that. That gap IS the lesson.)
    # - Collect the DEPENDENCIES lines for every petstore operation: you have
    #   just built a correlation graph by hand. Diff it against the [declared]/
    #   [inferred] edges the Autonomous Petshop derives deterministically
    #   (cookbook/integrations/11_autonomous_petshop.py) — where does the
    #   model's [guessed] edge disagree with the spec's declared one?
    return 0


if __name__ == "__main__":
    sys.exit(main())
