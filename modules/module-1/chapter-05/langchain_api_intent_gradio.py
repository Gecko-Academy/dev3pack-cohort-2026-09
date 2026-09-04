"""API Semantic Layer — the Gradio surface for langchain_api_intent.py.

Same prompt, same model, one function — plus a UI. The template and model are
initialized once at module level; the interface calls
generate_semantic_description(operation) per request.

Setup (optional material — not part of the course dependencies):
    uv add langchain langchain-openai gradio
    export OPENAI_API_KEY=sk-...     # or put it in .env

Run:
    uv run python modules/module-1/chapter-05/langchain_api_intent_gradio.py
"""

from __future__ import annotations

import os
import sys

# Graceful skips first: optional material must never crash a fresh clone.
try:
    import gradio as gr
    from langchain.chat_models import init_chat_model
    from langchain_core.prompts import PromptTemplate
except ImportError:
    print("SKIP: gradio and/or LangChain not installed (this is optional pre-work).")
    print("      To run it: uv add langchain langchain-openai gradio")
    sys.exit(0)

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

if not os.environ.get("OPENAI_API_KEY"):
    print("SKIP: OPENAI_API_KEY is not set (this app makes live calls).")
    print("      Set it in .env, then rerun.")
    sys.exit(0)

from langchain_api_intent import PROMPT_TEXT  # one prompt, two surfaces

# Initialized once, outside the function — per-request work is only the call.
prompt_template = PromptTemplate.from_template(PROMPT_TEXT)
model = init_chat_model("gpt-4o-mini", model_provider="openai")


def generate_semantic_description(operation: str) -> str:
    """Format the prompt with the operation, call the model, return the text."""
    if not operation or not operation.strip():
        return "Enter an API operation, e.g. GET /pets/{petId}"
    prompt = prompt_template.format(operation=operation.strip())
    response = model.invoke(prompt)
    return response.text


demo = gr.Interface(
    fn=generate_semantic_description,
    inputs=[gr.Textbox(label="API Operation", lines=1)],
    outputs=[gr.Textbox(label="Semantic Description", lines=8)],
    flagging_mode="never",
    title="API Semantic Layer",
    description=(
        "Enter an API operation (e.g. GET /pets/{petId}) to get its semantic "
        "description — what it does, what it returns, when an agent should use "
        "it, and its [declared]/[guessed] dependencies."
    ),
)

if __name__ == "__main__":
    demo.launch()
