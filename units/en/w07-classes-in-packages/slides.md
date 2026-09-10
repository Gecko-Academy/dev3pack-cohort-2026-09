---
marp: true
paginate: true
theme: default
---

# Week 0 · Course A, Chapter 3: Classes in a package
## Object-oriented Python, inheritance, and the DRY principle

Dev3Pack AI-Engineering Bootcamp · Week 0 (self-paced)

---

# Lesson 1
## Adding classes to a package

---

## The anatomy of a class

```python
# working in work_dir/my_package/my_class.py
# Define a minimal class with an attribute
class MyClass:
    """A minimal example class

    :param value: value to set as the ``attribute`` attribute
    :ivar attribute: contains the contents of ``value`` passed in init
    """

    # Method to create a new instance of MyClass
    def __init__(self, value):
        # Set attribute as the contents of the value parameter
        self.attribute = value
```

```python
# working in work_dir/my_package/__init__.py
from .my_class import MyClass
```

---

## Using a class in a package

```python
# working in work_dir/my_script.py
import my_package

# Create an instance of MyClass
my_instance = my_package.MyClass(value="class attribute value")

# Print the value of the class attribute
print(my_instance.attribute)
```

---

## Output

```
'class attribute value'
```

`self` is the instance being built. `self.attribute = value` stores the parameter on it, under the name the docstring promised. The `self` convention: the first parameter of every method is the instance, and you never pass it yourself.

---

## Why this matters on Monday

- Unit 3's `ToolDef` and the repo's `Tool` in `src/bootcamp_agent/tools.py` are `@dataclass(frozen=True)`: a class where `__init__` is generated from the field list, and the docstring's promise is the type annotation.
- `FakeLLM.__init__` in `src/bootcamp_agent/llm.py` does exactly what this lesson does by hand: `self.responses`, `self.default`, `self.calls`, each one a promise a caller can read.
- Read a class in this repo the way you read this one: find `__init__`, list what it sets on `self`, and that is the contract.

---

## Summary: what does a class promise?

| Piece | Promise |
|---|---|
| `class MyClass:` | a blueprint, importable from the package |
| `__init__(self, value)` | how an instance is built, and from what |
| `self.attribute = value` | what an instance carries afterwards |
| `:ivar attribute:` in the docstring | the same promise, written for the reader |

**Let's practice:** notebook, exercise 1.

---

# Lesson 2
## Classes and the DRY principle

---

## Inheritance in Python

```python
# Import the ParentClass object
from .parent_class import ParentClass


# Create a child class with inheritance
class ChildClass(ParentClass):
    def __init__(self):
        # Call parent's __init__ method
        ParentClass.__init__(self)
        # Add unique child class attribute
        self.child_attribute = "I am a child class attribute!"


# Create a ChildClass instance
child_class = ChildClass()
print(child_class.child_attribute)
print(child_class.parent_attribute)
```

---

## Output

```
I am a child class attribute!
I am a parent class attribute!
```

Don't Repeat Yourself. `SocialMedia` needs everything `Document` does plus hashtag counts; inheriting means the `Document` code is written once and `SocialMedia` adds only what is new. The parent's `__init__` must be called, because defining `__init__` on the child replaces it.

---

## Why this matters on Monday

- `LLMClient` in `src/bootcamp_agent/llm.py` is a `Protocol`: any class with `complete(system, user) -> str` fits, with no inheritance at all. That is duck typing, the other way Python shares a shape.
- `FakeLLM`, `AnthropicClient` and `OpenAICompatibleClient` all fit it, and `get_client(settings)` returns whichever the config asks for. The agent code never repeats itself per provider.
- When you add a provider in session 2, you write one class with one method, not a copy of the agent.

---

## Summary: inherit, or fit the shape?

| You want | Do |
|---|---|
| a child that IS a parent plus something | `class Child(Parent)` and call the parent's `__init__` |
| several classes that can stand in for each other | one `Protocol`, one method each, no shared base |
| the parent's state on the child | call `Parent.__init__(self)` first, or `super().__init__()` |
| to avoid copying a method | inherit it, or move it to a function both classes call |

**Let's practice:** notebook, exercise 2.

---

# Lesson 3
## Multilevel inheritance

---

## Multilevel inheritance and super()

```python
class Parent:
    def __init__(self):
        print("I'm a parent!")


class SuperChild(Parent):
    def __init__(self):
        super().__init__()
        print("I'm a super child!")


class Grandchild(SuperChild):
    def __init__(self):
        super().__init__()
        print("I'm a grandchild!")


grandchild = Grandchild()
```

---

## Output

```
I'm a parent!
I'm a super child!
I'm a grandchild!
```

`super().__init__()` finds the next class up the chain and passes `self` for you. `Parent.__init__()` with no `self` is a `TypeError`, and that slip is in the deck this lesson comes from.

---

## Keeping track of inherited attributes

```python
# Create a SocialMedia instance
sm = SocialMedia("@DataCamp #DataScience #Python #sklearn")

# What methods does sm have?
dir(sm)
```

```
['__class__', '__delattr__', ..., '__weakref__', '_count_hashtags',
 '_count_mentions', '_count_words', '_tokenize', 'hashtag_counts',
 'mention_counts', 'text', 'tokens', 'word_counts']
```

`dir()` lists everything, inherited or not. The underscore names are the internal steps; the rest is the promise.

---

## Why this matters on Monday

- The MRO is what `super()` walks. `Grandchild.__mro__` prints it; read it once and `super()` stops being magic.
- This repo's classes are one level deep on purpose: a Protocol and three adapters. When a chain gets to three levels, `dir()` and `__mro__` are how you find out where an attribute came from.
- The checker for exercise 3 builds each ancestor on its own and compares what it prints; that is the test you can run by hand on any class you inherit from.

---

## Summary: which call, at which level?

| Situation | Call |
|---|---|
| one parent, you want to name it | `Parent.__init__(self)` |
| one parent, you want the chain to work | `super().__init__()` |
| three levels, each printing in order | `super().__init__()` first, then the level's own work |
| which attribute came from where | `dir(instance)`, then `Class.__mro__` |

**Let's practice:** notebook, exercise 3.

---

# Lesson 4
## Leveraging classes

---

## Adding the _tokenize() method

```python
# Import function to perform tokenization
from .token_utils import tokenize


class Document:
    def __init__(self, text, token_regex=r"[a-zA-Z]+"):
        self.text = text
        self.tokens = self._tokenize()

    def _tokenize(self):
        return tokenize(self.text)


doc = Document("test doc")
print(doc.tokens)
```

---

## Output

```
['test', 'doc']
```

`tokens` is computed once, in `__init__`, and stored. `_tokenize` is non-public: the underscore tells the reader it is an internal step that may change. Its risks are the lesson's own list: lack of documentation, and unpredictability.

---

## Why this matters on Monday

- `_refusal()` in `src/bootcamp_agent/agent.py` and `_tokens()` in `src/bootcamp_agent/retrieval.py` are this convention in the repo you will work in: helpers the module uses and no caller should.
- Every checker in `src/bootcamp_agent/week0_checks/` is a `_w0N_eM` function: registered by id, never imported by name.
- When you steer an assistant through the package, the rule is the same: change what a `_` helper does freely, change a public name only with its callers.

---

## Summary: public, or non-public?

| The name | It means |
|---|---|
| `doc.tokens` | a promise: read it, rely on it |
| `doc._tokenize()` | an internal step: may change, do not call from outside |
| `tokenize()` in `token_utils` | a plain function, shared by any class that needs it |
| `token_regex` with a default | an option most callers never touch |

**Let's practice:** notebook, exercise 4.

---

## Exit ticket + homework

- One thing that works: a three-level chain that prints oldest first.
- One thing unclear: when to inherit and when to write a Protocol.
- Your next action: open `src/bootcamp_agent/llm.py`, list every class, and say which ones fit `LLMClient`.

**Next:** unit 08, documentation, tests and readability.
