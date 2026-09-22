# Start a new project from this template

This folder is the skeleton every real-world project copies. It is not a project
itself: it has no data, no checks and no answers. Its notebook runs top to bottom as
shipped, so CI proves the skeleton still works.

| File | What it is |
|---|---|
| `notebook.ipynb` | The skeleton notebook, with every section in order |
| `AGENTS.md` | The file a coding assistant reads about this project |
| `data/LICENSE.md` | Where the data came from, its licence, and the credit |

## Step by step

1. **Pick a number and a short name.** The folder is `projects/NN-short-name`, for
   example `projects/03-bus-timetables`. The check ids are `project-NN-e1`,
   `project-NN-e2`, and so on.
2. **Copy the template.**

   ```bash
   cp -r projects/_template projects/NN-short-name
   ```

3. **List every placeholder.** Each one says `write this`. The project is not done
   while one is left.

   ```bash
   grep -rn "write this\|NN-your-project\|project-NN\|_template" projects/NN-short-name
   ```

4. **Add the data.** Put the files in `data/`. Fill in `data/LICENSE.md`. For data
   fetched from a URL, add a `data/sources.json` with the URL, the date you fetched it
   and the size of each file (Project 02's is the model). Measure sizes; never guess.
5. **Register the checks.** Write `src/bootcamp_agent/projects/<short_name>.py`, one
   function per deliverable, each decorated with `@register("project-NN-eN")` from
   `bootcamp_agent.bonus`. Checks read plain lists and strings and import only the
   standard library, because CI installs no project extra. Then import the module in
   the notebook's setup cell. `check_step()` runs a registered check and calls
   `bonus()` for you.
6. **Write the steps.** One `## N. <imperative title>` per step, one purpose sentence,
   **What to look at:** bullets, short cells with a comment on the first line, a
   preview after every load, the check, a **Try it** cell, three hints and an
   **Ask your assistant** block. Hide heavy output: set the cell's metadata to
   `"jupyter": {"outputs_hidden": true}`, as the template's full-table cell does.
7. **Ship both lanes.** `[live]` runs the model on the learner's machine. `[recorded]`
   replays one real run from `data/recorded/`, with a `_provenance` block that says
   when it was made and with which model. The setup cell prints which lane is on.
8. **Decide on `# manual-run:`.** CI runs every notebook under `projects/` with the
   dev group only: no ChromaDB, no model. If your notebook needs the `projects` extra
   or Ollama, put `# manual-run: <what it needs>` on the first line of the **first code
   cell**. Then CI skips it, and your test file must pin what would break silently
   (Project 02 pins the recorded chunks). The template carries no marker, because it
   needs nothing and CI should run it.
9. **Fix the Colab badge.** Change `NN-your-project` in the first cell to your folder.
   If the notebook should run on Colab, copy the Colab cell from Project 01 or 02.
10. **Fill in `AGENTS.md`.** Every section. Keep the rules for the assistant.
11. **Write the test.** `tests/test_project_<short_name>.py`: each check passes a good
    value and fails each mistake it exists for, by its message. The `tests/` folder
    is not published to learners.
12. **List it.** Add a row to `projects/README.md` and to
    `units/en/tracks/projects/introduction.mdx`. Then regenerate:

    ```bash
    uv run python scripts/notebook_index.py
    uv run python scripts/course_site.py
    ```

## Before it ships

| Check | How to tell |
|---|---|
| The data has a licence | `data/LICENSE.md` names the licence, the publisher and the URL |
| The data says where it came from | Every file has a source, a fetch date and a measured size |
| Both lanes run | The notebook runs with the model and without it, and the setup cell says which |
| The checks are registered | `src/bootcamp_agent/projects/<short_name>.py` registers `project-NN-eN` in `BONUS`, never in `CHECKS` |
| There is a test file | `tests/test_project_<short_name>.py`, and `uv run pytest -q` is green |
| It is listed | A row in `projects/README.md` and in the projects track page |
| No question is quoted in a page | No `.mdx` page quotes a labelled question. The course coach indexes every page, and a quoted question wins the search for itself |
| No placeholder is left | `grep -rn "write this" projects/NN-short-name` prints nothing |
| `AGENTS.md` is complete | `tests/test_project_template.py` passes |
| No secret, no email address | Nothing from `.env`, and no contact address in any file |

## Style

Write for beginners. Tables first, short sentences, active voice, plain words and
sentence-case headings. State numbers only after you have measured them.
