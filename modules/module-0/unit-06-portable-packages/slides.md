---
marp: true
paginate: true
theme: default
---

# Week 0 · Course A, Chapter 2: A portable package
## Requirements, setup, and your first package

Dev3Pack AI-Engineering Bootcamp · Week 0 (self-paced)

---

# Lesson 1
## Making your package portable

---

## Steps to portability

- A portable package is one another machine can install and run.
- Two files make it so: `requirements.txt` says what it needs, `setup.py` says what it is.
- The structure: `work_dir/` holds `my_package/`, `requirements.txt` and `setup.py` side by side.

---

## The contents of requirements.txt

```python
# working in work_dir/requirements.txt
# Needed packages/versions
matplotlib
numpy==1.15.4
pycodestyle>=2.4.0
```

```python
# working in the terminal
datacamp@server:~$ pip install -r requirements.txt
```

---

## Output

```
Collecting matplotlib
Collecting numpy==1.15.4
Collecting pycodestyle>=2.4.0
Successfully installed matplotlib-<newest> numpy-1.15.4 pycodestyle-<newest>
```

Three lines, three rules: a bare name floats, `==` pins one version, `>=` sets a floor and floats above it. Two of the three resolve to whatever is newest on the day you run it.

---

## The contents of setup.py

```python
from setuptools import setup

setup(
    name="my_package",
    version="0.0.1",
    description="An example package for DataCamp.",
    author="Adam Spannbauer",
    author_email="spannbaueradam@gmail.com",
    packages=["my_package"],
    install_requires=["matplotlib", "numpy==1.15.4", "pycodestyle>=2.4.0"],
)
```

```python
datacamp@server:~/work_dir $ pip install .
```

---

## Output

```
Building wheels for collected packages: my-package
  Running setup.py bdist_wheel for my-package ... done
Successfully built my-package
Installing collected packages: my-package
Successfully installed my-package-0.0.1
```

`install_requires` is what the package needs to run. `requirements.txt` is what a developer of the package needs, and can carry `--index-url` and dev tools too.

---

## Why this matters on Monday

- This repo's `pyproject.toml` is the modern `setup.py`, and `uv.lock` is `requirements.txt` with every version resolved. `uv sync --group dev` installs both.
- `dependencies = ["python-dotenv>=1.0.1"]` is the runtime need; `[dependency-groups] dev` holds `pytest`, `ruff`, `nbformat`. Unit 1, lesson 3 made you sort exactly these.
- The rule is the same as the lesson's: runtime needs go with the package, developer tools go with the developer.

---

## Summary: which file does it go in?

| The thing | Where |
|---|---|
| a package your code imports at runtime | `install_requires` (today: `dependencies` in `pyproject.toml`) |
| a tool only developers run (`pytest`, `ruff`) | `requirements.txt` (today: a dev dependency group) |
| the exact versions a machine resolved | a lockfile (`uv.lock`) |
| the package name, version and author | `setup.py` (today: `[project]` in `pyproject.toml`) |

**Let's practice:** notebook, exercise 1.

---

# Lesson 2
## Adding functionality to packages

---

## Adding functionality

```python
# working in work_dir/my_package/utils.py
def we_need_to_talk(break_up=False):
    """Helper for communicating with partner"""
    if break_up:
        print("It's not you, it's me...")
    else:
        print("I <3 You!")
```

```python
# working in work_dir/my_script.py
# Import the utils submodule
import my_package.utils

# Decide to move on
my_package.utils.we_need_to_talk(break_up=True)
```

---

## Output

```
It's not you, it's me...
```

The function lives in a submodule, so the script names the submodule. Three dots deep is a lot to type for every call.

---

## Importing functionality with __init__.py

```python
# working in work_dir/my_package/__init__.py
from .utils import we_need_to_talk
```

```python
# working in work_dir/my_script.py
# Import the custom package
import my_package

# Realise you found your soulmate
my_package.we_need_to_talk(break_up=False)
```

---

## Output

```
I <3 You!
```

`__init__.py` runs when the package is imported. Whatever it imports becomes an attribute of the package. The dot in `.utils` means "the module next to me".

---

## Why this matters on Monday

- `src/bootcamp_agent/__init__.py` holds a docstring and `__version__`, and nothing else. It does not re-export the LLM seam.
- So the course imports by submodule, the first shape in this lesson: `from bootcamp_agent.llm import FakeLLM`, `from bootcamp_agent.checks import check`.
- That is a choice, not an accident: a thin `__init__.py` keeps `import bootcamp_agent` cheap and makes every import say where the name came from.

---

## Summary: which import do I write?

| You want | Write |
|---|---|
| a function from a submodule, named in full | `import my_package.utils` then `my_package.utils.we_need_to_talk()` |
| the same function at the package top | `from .utils import we_need_to_talk` in `__init__.py` |
| to read where a name really lives | follow the dots: package, submodule, function |
| a package that stays cheap to import | keep `__init__.py` thin, as this repo does |

**Let's practice:** notebook, exercise 2.

---

# Lesson 3
## Writing your first package

---

## Importing a local package

```python
import my_package

help(my_package)
```

---

## Output

```
Help on package my_package:

NAME
    my_package

PACKAGE CONTENTS


FILE
    ~/work_dir/my_package/__init__.py
```

`help()` found the package, and had nothing to say about it. NAME, PACKAGE CONTENTS and FILE come for free. A DESCRIPTION comes only from a docstring at the top of `__init__.py`.

---

## Why this matters on Monday

- Run `help(bootcamp_agent)` in any notebook: the DESCRIPTION is the package docstring in `src/bootcamp_agent/__init__.py`, and PACKAGE CONTENTS lists the modules unit 2 made you read off the disk.
- A learner who can read `help(package)` never has to guess what a module is for, and never asks an assistant to guess either.
- The minimal package is two files: `__init__.py` and one module. Everything else is added when it earns its place.

---

## Summary: what does help(my_package) show?

| Section | Comes from |
|---|---|
| NAME | the directory name |
| DESCRIPTION | the docstring at the top of `__init__.py` |
| PACKAGE CONTENTS | the `.py` files next to `__init__.py` |
| FILE | where the package really lives on disk |

**Let's practice:** notebook, exercise 3.

---

## Exit ticket + homework

- One thing that works: a package you built that a script imported by name.
- One thing unclear: the difference between `install_requires` and `requirements.txt`, in your own words.
- Your next action: open `pyproject.toml` in this repo and find the runtime dependency and the dev group.

**Next:** unit 07, classes in a package.
