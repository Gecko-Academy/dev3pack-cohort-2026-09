---
marp: true
paginate: true
theme: default
---

# Week 0 · Course A, Chapter 1: Packages, PyPI and PEP 8
## Introduction to packages and documentation

Dev3Pack AI-Engineering Bootcamp · Week 0 (self-paced)

---

# Lesson 1
## Packages and PyPI

---

## Reading documentation with help()

```python
datacamp@server:~$ pip install numpy

Collecting numpy
   100% |████████████████████████████████| 24.5MB 44kB/s
Installing collected packages: numpy
Successfully installed numpy-1.15.4
```

```python
help(numpy.busday_count)
```

---

## Output

```
busday_count(begindates, enddates)
    Counts the number of valid days between `begindates` and
    `enddates`, not including the day of `enddates`.

    Parameters
    ----------
    begindates : the first dates to count from.
    enddates : the end dates to count to (excluded from the count)

    Returns
    -------
    out : the number of valid days between the start and end dates.

    Examples
    --------
    >>> # Number of business days in 2011
    ...   np.busday_count('2011', '2012')
    260
```

The first line is the signature. Everything you need to make the call is there, before the prose.

---

## Why this matters on Monday

- This repo uses `uv`, not `pip`. Same index (PyPI), same packages, plus a lockfile on top: `uv.lock` records the exact version every machine installs.
- `uv sync --group dev` is the `pip install` you will type most.
- `help()` works offline on anything: `help(np)` prints the package summary, `help(42)` prints the `int` class. Try it before you search the web.

---

## Summary: where do I look first?

| I want to know | Do this |
|---|---|
| what a function takes | `help(function)` and read the first line |
| what a package is for | `help(package)` and read the first paragraph |
| what type a value is | `help(value)` shows its class and methods |
| where the package came from | PyPI, via `pip install` or `uv add` |

**Let's practice:** notebook, exercise 1.

---

# Lesson 2
## Conventions and PEP 8

---

## Violating PEP 8

```python
#define our data
my_dict ={
   'a'    : 10,
'b': 3,
   'c'    :   4,
              'd': 7}
#import needed package
import numpy as np
#helper function
def DictToArray(d):
   """Convert dictionary values to a numpy array"""
   #extract values and convert
                  x=np.array(d.values())
                  return x
print(DictToArray(my_dict))
```

---

## Output

```
array([10,    4,    3,   7])

datacamp@server:~$ pycodestyle dict_to_array.py
dict_to_array.py:5:9: E203 whitespace before ':'
dict_to_array.py:6:14: E131 continuation line unaligned for hanging indent
dict_to_array.py:8:1: E265 block comment should start with '# '
dict_to_array.py:9:1: E402 module level import not at top of file
dict_to_array.py:11:1: E302 expected 2 blank lines, found 0
dict_to_array.py:13:15: E111 indentation is not a multiple of four
```

The code runs. Python does not care. The next reader does, and `pycodestyle` speaks for the reader.

---

## Following PEP 8

```python
# Import needed package
import numpy as np


# Define our data
my_dict = {"a": 10, "b": 3, "c": 4, "d": 7}


# Helper function
def dict_to_array(d):
    """Convert dictionary values to a numpy array"""
    # Extract values and convert
    x = np.array(d.values())
    return x


print(dict_to_array(my_dict))
```

---

## Output

```
array([10,    4,   3,   7])

datacamp@server:~$ pycodestyle dict_to_array.py
datacamp@server:~$
```

Same result, and the linter has nothing to say. "Code is read much more often than it is written."

---

## Why this matters on Monday

- This repo runs `ruff`, which reports the same codes: `E203`, `E265`, `E402`, `E302`, `E111` all exist in `ruff check`.
- CI runs `uv run ruff check .` and `uv run ruff format --check .` on every push. A style violation fails the build before a reviewer sees it.
- `uv run ruff format` fixes most of them for you. Run it before you ask anybody to read your code.

---

## Summary: what does the reader expect?

| Situation | Convention |
|---|---|
| a comment | `# ` then a space, then the sentence |
| an import | at the top of the file, before any code |
| a function name | `snake_case`, never `CamelCase` |
| a function definition | two blank lines above and below |
| indentation | four spaces, every level |

**Let's practice:** notebook, exercise 2.

---

# Lesson 3
## Python, data science and software engineering

---

## Four words the whole course uses

- **Modularity**: improve readability, improve maintenance, solve a problem once.
- **Documentation**: show users how to use your project, avoid confusion between collaborators, avoid future frustration.
- **Testing**: save time on manual tests, find and fix more bugs, run them anywhere, at any time.
- **Version control and git**: the history of every change, and the way work is reviewed.

---

## Modularity in Python

```python
# Import the pandas PACKAGE
import pandas as pd

# Create some example data
data = {"x": [1, 2, 3, 4], "y": [20.1, 62.5, 34.8, 42.7]}

# Create a dataframe CLASS object
df = pd.DataFrame(data)

# Use the plot METHOD
df.plot("x", "y")
```

---

## Output

```
<Axes: xlabel='x'>
```

A line chart of `y` against `x`. Three shapes made it: a package you import, a class you instantiate, a method you call on the instance.

---

## Why this matters on Monday

- `bootcamp_agent` is a package. `FakeLLM` is a class. `llm.complete(system, user)` is a method. That is the whole repo, in three shapes.
- `tests/` holds the automated tests, `uv run pytest` runs them, and CI runs them again on every push.
- Every session's notebook is documentation with a check beside it. Git is how the work reaches the reviewer.

---

## Summary: which shape is this?

| The line looks like | It is |
|---|---|
| `import name` | a package |
| `Name(arguments)` | a class, being instantiated |
| `thing.name(arguments)` | a method, called on `thing` |
| `name(arguments)` with no dot | a function |

**Let's practice:** notebook, exercise 3.

---

## Exit ticket + homework

- One thing that works: a call you made from the signature `help()` printed, not from memory.
- One thing unclear: which of the four words you could not yet explain to a colleague.
- Your next action: run `uv run ruff check src` on this repo and read one finding.

**Next:** unit 06, a portable package.
