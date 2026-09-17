"""Real-world projects: open data, a local model, a vector database, and no API key.

Each project is a brief with named deliverables -- `embeddings`, `embeddings_2d`,
`most_similar_reviews` -- checked the way a reviewer would check them: by what the
values ARE, not by how confidently a notebook printed them.

The checks import nothing outside the standard library. The project itself needs
the `projects` extra (ChromaDB, scikit-learn, pandas); CI installs none of that,
and it does not have to, because a check reads plain lists and strings.
"""
