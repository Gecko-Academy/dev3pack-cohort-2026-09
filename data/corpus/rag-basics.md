<!-- title: RAG Basics -->
<!-- tags: retrieval, rag, chunking, citations, grounding -->

# RAG Basics

Retrieval-augmented generation (RAG) grounds a model's answer in documents you
control. Instead of hoping the model memorized the right facts, the application
retrieves relevant passages at question time and places them in the prompt. The
model's job shrinks from "know everything" to "synthesize from what you were
shown" — a job it is much better at.

## The pipeline

A minimal RAG pipeline has four stages. **Chunking** splits documents into
passages small enough to be individually relevant — respecting paragraph
boundaries beats cutting at a fixed character count mid-sentence. **Indexing**
prepares chunks for search; a lexical index (keyword overlap) is a perfectly
respectable baseline and is deterministic, cheap, and debuggable. Embedding-based
semantic search improves recall on paraphrased questions but adds a dependency
and a failure mode you cannot inspect by eye. **Retrieval** selects the top-k
chunks for a query. **Generation** answers using only the retrieved context, with
citations naming the source documents.

## Retrieval failure vs generation failure

When a RAG system answers wrongly, the first diagnostic question is: did the
right passage reach the prompt? If retrieval missed it, no amount of prompt
engineering will fix the answer — fix chunking, the index, or the query instead.
If the right passage was present and the answer still went wrong, the failure is
in generation: instructions, formatting, or the model ignoring context. Keeping
retrieved chunks inspectable (log them, show them) is what makes this diagnosis a
two-minute check instead of a guessing game.

## Citations keep the system honest

Every answer should name the document ids it drew from, and the application
should verify those ids against what was actually retrieved. A citation the
retriever never returned is a fabrication and should be stripped and flagged.
The "I don't know" case matters most: when nothing relevant is retrieved, the
system must refuse rather than let the model improvise from its training data.

## Small corpus, high leverage

Most of RAG's value appears with a corpus of five documents, not five million.
Start small, keep the corpus versioned in git, and grow it only when a measured
retrieval failure says you need to.
