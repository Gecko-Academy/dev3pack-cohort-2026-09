"""LangChain template — explain a concept (optional Session 5 pre-work).

LangChain's `init_chat_model` is the framework's version of the provider seam
you built in `bootcamp_agent/llm.py`: one line picks the provider, and the
rest of the code never knows which model it got.

Setup (not part of the course dependencies — this is optional material):
    uv add langchain langchain-openai
    export OPENAI_API_KEY=sk-...     # or put it in .env

Run:
    uv run python modules/module-1/chapter-05/langchain_template.py

Without a key (or without langchain installed) the script explains what it
would do and exits cleanly — the same graceful-skip convention as the course
notebooks.
"""

from __future__ import annotations

import os
import sys


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
        pass  # python-dotenv ships with the course env; harmless if absent here

    if not os.environ.get("OPENAI_API_KEY"):
        print("SKIP: OPENAI_API_KEY is not set (this template makes a live call).")
        print("      Set it in .env, then rerun. Nothing else in the course needs it.")
        return 0

    # 2. Create a PromptTemplate with a variable for the concept to explain
    prompt_template = PromptTemplate.from_template(
        "You are an AI-engineering instructor. Explain the concept of {concept} "
        "to a developer, in at most 5 paragraphs. Include at least one concrete "
        "code or architecture example for each side of the concept, and close by "
        "saying when to use one and when to use the other."
    )

    # 3. Initialize the model (gpt-4o-mini, provider openai)
    model = init_chat_model("gpt-4o-mini", model_provider="openai")

    # 4. Format the prompt with a concept of your choice and call the model
    concept = "loop engineering vs graph engineering in AI agents"
    prompt = prompt_template.format(concept=concept)
    response = model.invoke(prompt)

    # 5. Print response.text
    # (On langchain-core 1.x `.text` is a property; on 0.3.x it was a method —
    # if you ever see "<bound method ...>" printed, call response.text() or upgrade.)
    print(response.text)

    # Follow-up exercise: grade the answer against the course's own guides —
    # docs/guides/loop-engineering.md and docs/guides/graph-engineering.md.
    # What did the model get right? What did it miss?
    return 0


if __name__ == "__main__":
    sys.exit(main())
