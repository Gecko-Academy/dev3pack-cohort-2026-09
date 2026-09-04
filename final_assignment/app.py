"""Gradio UI for the final assignment — the Hugging Face Space version.

Runs the SAME agent and grader as the CLI (`grade.py`); this file is only a
surface. Publish this folder as a Space to make your milestone public.
Provider keys go in the Space's Settings -> Secrets, never in the repo.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_ROOT = HERE if (HERE / "src" / "bootcamp_agent").is_dir() else HERE.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(HERE))

import gradio as gr  # noqa: E402
from agent import YourAgent  # noqa: E402
from grade import PASS_THRESHOLD, grade, load_questions  # noqa: E402


def ask(question: str) -> str:
    if not question.strip():
        return "Ask a question about the bootcamp corpus."
    answer = YourAgent()(question)
    return (
        f"answer: {answer.answer}\n"
        f"citations: {list(answer.citations)}\n"
        f"confidence: {answer.confidence}\n"
        f"needs_human_review: {answer.needs_human_review}"
    )


def run_practice_set() -> tuple[str, list[list[str]]]:
    entries = load_questions(HERE / "questions.jsonl")
    results = grade(YourAgent(), entries)
    passed = sum(r.passed for r in results)
    score = passed / len(results) if results else 0.0
    verdict = "PASSED" if score >= PASS_THRESHOLD else "NOT YET"
    status = (
        f"score: {passed}/{len(results)} ({score:.0%}) — pass bar {PASS_THRESHOLD:.0%} — {verdict}"
    )
    rows = [["PASS" if r.passed else "FAIL", r.task_id, r.question, r.detail] for r in results]
    return status, rows


with gr.Blocks(title="Dev3Pack Final Assignment") as demo:
    gr.Markdown(
        "# Dev3Pack AI-Engineering Bootcamp — Final Assignment\n"
        "A source-grounded research assistant: it cites what it read and refuses "
        "what it can't support. Ask it something, or run the practice set."
    )
    with gr.Row():
        question_box = gr.Textbox(
            label="Ask the agent", placeholder="How does chunking work in RAG?"
        )
    answer_box = gr.Textbox(label="Answer", lines=5)
    ask_button = gr.Button("Ask")
    ask_button.click(ask, inputs=question_box, outputs=answer_box)

    gr.Markdown("---")
    run_button = gr.Button("Run the practice set (10 questions)")
    status_box = gr.Textbox(label="Score")
    results_table = gr.Dataframe(
        headers=["result", "task", "question", "detail"], label="Per-question results"
    )
    run_button.click(run_practice_set, outputs=[status_box, results_table])


if __name__ == "__main__":
    demo.launch()
