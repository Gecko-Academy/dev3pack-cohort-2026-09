"""Three bounded, read-only tools.

Tool design rules taught in session 5, enforced here:
- narrow input contracts, validated at the boundary (empty query, unknown id);
- hard caps the caller cannot exceed (max_results is clamped, never trusted);
- helpful errors that name the valid options instead of just refusing;
- read-only: nothing here writes, spends, or mutates.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from bootcamp_agent.documents import Document
from bootcamp_agent.llm import LLMClient
from bootcamp_agent.retrieval import retrieve

MAX_SEARCH_RESULTS = 5


class ToolError(Exception):
    """Raised when a tool's arguments are invalid. Message is safe to show the model."""


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    run: Callable[..., str]


def build_tools(documents: Sequence[Document], client: LLMClient) -> dict[str, Tool]:
    """Build the tool registry over a corpus. All tools are read-only."""
    by_id = {doc.doc_id: doc for doc in documents}

    def search_documents(query: str, max_results: int = 3) -> str:
        if not query or not query.strip():
            raise ToolError("search_documents: 'query' must be a non-empty string")
        capped = max(1, min(int(max_results), MAX_SEARCH_RESULTS))
        results = retrieve(query, documents, top_k=capped)
        if not results:
            return "No matching passages found."
        return "\n\n".join(
            f"[{scored.chunk.doc_id}] (score {scored.score:.2f})\n{scored.chunk.text}"
            for scored in results
        )

    def get_document_metadata(doc_id: str) -> str:
        doc = by_id.get(doc_id)
        if doc is None:
            raise ToolError(
                f"get_document_metadata: unknown doc_id {doc_id!r}; valid ids: {sorted(by_id)}"
            )
        return (
            f"doc_id: {doc.doc_id}\ntitle: {doc.title}\nsource: {doc.source}\n"
            f"tags: {', '.join(doc.tags)}\nlength_chars: {len(doc.text)}"
        )

    def summarize_document(doc_id: str) -> str:
        doc = by_id.get(doc_id)
        if doc is None:
            raise ToolError(
                f"summarize_document: unknown doc_id {doc_id!r}; valid ids: {sorted(by_id)}"
            )
        summary = client.complete(
            system="Summarize the document in at most three sentences. Be factual.",
            user=f"Document {doc.doc_id} ({doc.title}):\n\n{doc.text}",
        )
        return f"[{doc.doc_id}] {summary}"

    return {
        "search_documents": Tool(
            name="search_documents",
            description="Search the corpus for passages relevant to a query "
            f"(max_results capped at {MAX_SEARCH_RESULTS}).",
            run=search_documents,
        ),
        "get_document_metadata": Tool(
            name="get_document_metadata",
            description="Return title, source, tags, and length for a known doc_id.",
            run=get_document_metadata,
        ),
        "summarize_document": Tool(
            name="summarize_document",
            description="LLM-summarize one document by doc_id (read-only).",
            run=summarize_document,
        ),
    }
