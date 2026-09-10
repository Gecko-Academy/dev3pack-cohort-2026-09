---
marp: true
paginate: true
theme: default
---

# Week 0 · Course A, Chapter 4: Documentation, tests and readability
## Maintainability: docstrings, doctest, pytest, and the Zen of Python

Dev3Pack AI-Engineering Bootcamp · Week 0 (self-paced)

---

# Lesson 1
## Documentation

---

## Comments and docstrings

- A comment is for the reader of the source: `# Calculate the square of x`. Nobody else sees it.
- A docstring is for the user of the function: `help()` prints it, tools render it, `doctest` runs its examples.
- Comment the **why**, not the **what**. `# Set people to 5` restates the code. `# There will be 5 people at the party` explains it.

---

## A docstring example

```python
def square(x):
    """Square the number x

    :param x: number to square
    :return: x squared

    >>> square(2)
    4
    """
    # `x * x` is faster than `x ** 2`
    # reference: https://stackoverflow.com/a/29055266/5731525
    return x * x
```

```python
help(square)
```

---

## Output

```
square(x)
    Square the number x

    :param x: number to square
    :return: x squared

    >>> square(2)
    4
```

The comments stayed in the source. The docstring came out as documentation. `:param` and `:return` are the two questions a signature cannot answer, and the `>>>` line is an example a machine can check.

---

## Why this matters on Monday

- Unit 2, lesson 3 was "a docstring that earns its place": summary line, what it returns, what it raises. This lesson adds the example, and the example is a test.
- `help(bootcamp_agent.retrieval.retrieve)` in any notebook shows the same shape on a function you will call in session 6.
- A coding assistant writes docstrings that restate the name. Read them the way you read `# Set people to 5`, and ask for the why.

---

## Summary: comment, or docstring?

| You are writing | Use |
|---|---|
| why a line is the way it is | a `#` comment above it |
| what a function takes, returns, raises | the docstring, `:param` and `:return` |
| one call and its result | a `>>>` example in the docstring |
| what a value is set to | nothing; the code already says it |

**Let's practice:** notebook, exercise 1.

---

# Lesson 2
## Unit tests

---

## Why test

- Confirm the code does what you expect.
- Make sure a change to one function does not break another.
- Protect against a change in a dependency.
- Two tools in Python: `doctest`, which runs the docstring's examples, and `pytest`, which runs test files.

---

## Using doctest

```python
def square(x):
    """Square the number x

    :param x: number to square
    :return: x squared

    >>> square(3)
    9
    """
    return x**3


import doctest

doctest.testmod()
```

---

## Output

```
Failed example:
    square(3)
Expected:
    9
Got:
    27
```

The docstring said 9. The body returned 27. `doctest` read the example, ran it, and reported both sides. The example was right; the body was a cube.

---

## Writing unit tests

```python
# working in workdir/tests/test_document.py
from text_analyzer import Document


# Test tokens attribute on Document object
def test_document_tokens():
    doc = Document("a e i o u")
    assert doc.tokens == ["a", "e", "i", "o", "u"]


# Test edge case of empty document
def test_document_empty():
    doc = Document("")
    assert doc.tokens == []
    assert doc.word_counts == Counter()
```

```python
datacamp@server:~/work_dir $ pytest
```

---

## Output

```
collected 2 items

tests/test_document.py ..                    [100%]

========== 2 passed in 0.61 seconds ==========
```

Two dots, two passes. `pytest` collects every `test_*.py` under `tests/`, runs every `test_*` function, and an `assert` is the whole test. Compare attributes, not objects: `doc_a == doc_b` is `False` for two identical Documents, `doc_a.tokens == doc_b.tokens` is `True`.

---

## Failing tests

```
datacamp@server:~/work_dir $ pytest
collected 2 items

tests/test_document.py F.
============== FAILURES ==============
________ test_document_tokens ________
def test_document_tokens(): doc = Document('a e i o u')
assert doc.tokens == ['a', 'e', 'i', 'o']
E AssertionError: assert ['a', 'e', 'i', 'o', 'u'] == ['a', 'e', 'i', 'o']
E Left contains more items, first extra item: 'u'
E Use -v to get the full diff
tests/test_document.py:7: AssertionError
====== 1 failed in 0.57 seconds ======
```

`F.` means the first test failed and the second passed. Left is what the code produced, right is what the test claimed. Here the test was wrong.

---

## Why this matters on Monday

- `uv run pytest` is the course's verdict on every session's work, and CI runs the same command on every push.
- Every `check("ch03-e1", value)` in a notebook is a unit test with a friendlier message: it runs your value and names the fix.
- When an assistant makes a test pass by editing the assertion, that is the `['a', 'e', 'i', 'o']` line above, in reverse. Read the diff before you believe the green.

---

## Summary: which test, and what does the output mean?

| You see | It means |
|---|---|
| `doctest` prints nothing | every docstring example passed |
| `Expected: 9  Got: 27` | the example and the body disagree; decide which is right |
| `..` and `2 passed` | every test ran and every assert held |
| `F.` and an `AssertionError` | left is what the code did, right is what the test claimed |

**Let's practice:** notebook, exercise 2.

---

# Lesson 3
## Readability counts

---

## The Zen of Python

```python
import this
```

```
The Zen of Python, by Tim Peters (abridged)

Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Readability counts.
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
```

---

## Descriptive naming

```python
# Poor naming
def check(x, y=100):
    return x >= y
```

```python
# Descriptive naming
def is_boiling(temp, boiling_point=100):
    return temp >= boiling_point
```

```python
# Overdoing it
def check_if_temperature_is_above_boiling_point(
    temperature_to_check, celsius_water_boiling_point=100
):
    return temperature_to_check >= celsius_water_boiling_point
```

---

## Output

```
>>> check(100)
True
>>> is_boiling(100)
True
>>> check_if_temperature_is_above_boiling_point(100)
True
```

All three return the same value. Only one of them can be read aloud in a sentence. A name says what a thing is for; a type says what it is made of, and the reader already knows that.

---

## Keep it simple: making a pizza

```python
def make_pizza(ingredients):
    dough = make_dough(ingredients)
    sauce = make_sauce(ingredients)
    assembled_pizza = assemble_pizza(dough, sauce, ingredients)
    return bake(assembled_pizza)
```

- The complex version mixed, kneaded, proved, sauteed, combined and simmered inside one function.
- Each step became a function with a name. `make_pizza` now reads as the recipe.
- When to refactor: when a function is hard to explain in one sentence, split it until each piece is easy.

---

## Why this matters on Monday

- README, "Safe Assistant Workflow", step 4: **inspect the diff yourself**. A diff full of `x`, `y` and `tmp` is one you cannot inspect.
- `bootcamp_agent.agent.answer_question(question, documents, llm)`: three names, and you know what it does before reading the body. That is the standard to hold an assistant to.
- `uv run ruff format` fixes spacing. Nothing fixes a bad name except a person who read it.

---

## Summary: is this name right?

| The name | Verdict |
|---|---|
| `check(x, y=100)` | says nothing; the reader must run it in their head |
| `is_boiling(temp, boiling_point=100)` | says what it is for and what True means |
| `check_if_temperature_is_above_boiling_point(...)` | true, and too long to read in one breath |
| `make_pizza` calling `make_dough`, `make_sauce` | simple, because each complex step got a name |

**Let's practice:** notebook, exercise 3.

---

# Lesson 4
## Documentation and tests in practice

---

## Documenting classes

```python
class Document:
    """Analyze text data

    :param text: text to analyze

    :ivar text: text originally passed to the instance on creation
    :ivar tokens: Parsed list of words from text
    :ivar word_counts: Counter containing counts of hashtags used in text
    """

    def __init__(self, text): ...
```

---

## Output

```
Help on class Document:

class Document(builtins.object)
 |  Analyze text data
 |
 |  :param text: text to analyze
 |
 |  :ivar text: text originally passed to the instance on creation
 |  :ivar tokens: Parsed list of words from text
 |  :ivar word_counts: Counter containing counts of hashtags used in text
```

`:param` documents what `__init__` takes; `:ivar` documents what the instance carries afterwards. Sphinx turns this into a website; `help()` shows it as is.

---

## Continuous integration and the tools around it

- Continuous integration runs the tests on every push, on a machine that is not yours, and reports the result on the repository.
- Sphinx: generate beautiful documentation. Travis CI: test your code continuously. GitHub and GitLab: host your projects with git.
- Codecov: find where to improve your tests. Code Climate: analyze your code for readability improvements.

---

## Why this matters on Monday

- The badge at the top of this repo's README is GitHub Actions running `.github/workflows/test.yml`: `ruff check`, `ruff format --check`, `pytest`, the index checks, and every notebook executed, on every push and pull request.
- The solutions notebooks run there with `BOOTCAMP_CHECKS_STRICT=1`, so a failing check fails the build. That is the same doctest idea, one level up.
- `:ivar` is the docstring shape for `FakeLLM`: `responses`, `default`, `calls`. When you write a class in session 5, document it this way.

---

## Summary: what runs where?

| Check | Runs |
|---|---|
| a docstring example | `doctest`, on your machine |
| a `tests/test_*.py` file | `uv run pytest`, on your machine |
| the same tests on every push | CI, on a machine that is not yours |
| the class docstring | `help(Document)`, and Sphinx for a site |

**Let's practice:** notebook, exercises 1 and 2 again, then read `.github/workflows/test.yml`.

---

# Lesson 5
## Final considerations

---

## Looking back: three ideas

- **Modularity**: `def function(): ...` and `class Class: ...`, in a package a script can import.
- **Documentation**: `"""docstrings"""` for the user, `# comments` for the reader of the source.
- **Automated testing**: `>>> f(x)` examples that `doctest` runs, and `test_*.py` files that `pytest` runs.

---

## Why this matters on Monday

- Session 1 opens with these three words and a fourth, git. The whole capstone package is built by adding a module, its docstring and its tests, one session at a time.
- The checks in every notebook are the automated tests of your own learning. `review("w08")` is the scorecard for this unit.
- Good luck. Data science and software engineering are the same craft once the code has a second reader.

---

## Summary: what did Course A leave you with?

| Chapter | The habit |
|---|---|
| 1. Packages and PEP 8 | `help()` before you call, `ruff` before you share |
| 2. A portable package | a `pyproject.toml`, a thin `__init__.py`, a docstring `help()` shows |
| 3. Classes in a package | `__init__` keeps the docstring's promise; `super()` keeps the parent's |
| 4. Docs, tests, readability | a `>>>` example, a red-then-green test, a name that says what |

**Let's practice:** `review("w08")`, then `review("w05")` to `review("w07")` for anything left red.

---

## Exit ticket + homework

- One thing that works: a test you took from red to green by reading the assertion, not by deleting it.
- One thing unclear: the difference between a comment and a docstring, in one sentence.
- Your next action: open `.github/workflows/test.yml` and list the five commands CI runs on your push.

**Next:** unit 09, the MCP course, when it lands.
