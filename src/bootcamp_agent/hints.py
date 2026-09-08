"""Hints you can always have, and that cost you something.

    check("ch03-e1", value)   # the verdict, and the fix, named
    hint("ch03-e1")           # the next nudge, -30 XP
    hint("ch03-e1", reveal=True)   # the worked answer, -70 XP

THE MODEL IS DATACAMP'S, AND IT IS BETTER THAN HIDING THE ANSWER. Their exercise
pane carries a "Receber Dica (-30 XP)" button: the hint is always one click
away, never gated, and it costs part of the exercise's points. That keeps the
incentive to think without ever leaving somebody stuck and stuck, which is what
a gate does.

Nothing here blocks. There is no unlock, no waiting period and no server. If you
want the answer immediately you can have it immediately, and the scorecard will
say so.

WHAT IS RECORDED, AND WHERE. A single SQLite file at ~/.bootcamp/progress.db, on
your machine, gitignored, and it never leaves unless you run
`bootcamp progress --export` yourself. It stores exercise ids and outcomes.

It does NOT store your answers, your name, your email, or anything you typed.
That is the same rule the depth track's data module makes you write down, and it
would be a poor course that taught a retention policy it did not keep.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path

#: What an exercise is worth, and what each level of help costs. A hint leaves
#: most of the credit; a reveal leaves a little, because reading the answer
#: after trying is still worth more than skipping.
FULL_MARKS = 100
HINT_COST = 30
REVEAL_COST = 70

STORE_ENV = "BOOTCAMP_PROGRESS_DB"


def store_path() -> Path:
    """Where progress lives. Overridable, mostly so tests do not touch yours."""
    override = os.environ.get(STORE_ENV)
    return Path(override) if override else Path.home() / ".bootcamp" / "progress.db"


def _connect() -> sqlite3.Connection:
    path = store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute(
        "create table if not exists attempts ("
        " exercise text primary key,"
        " passed integer not null default 0,"
        " attempts integer not null default 0,"
        " hinted integer not null default 0,"
        " revealed integer not null default 0,"
        " first_seen text not null default (datetime('now')),"
        " last_seen text not null default (datetime('now')))"
    )
    connection.commit()
    return connection


@dataclass(frozen=True)
class Attempt:
    """One exercise's history. Outcomes only; never what was typed."""

    exercise: str
    passed: bool
    attempts: int
    hinted: bool
    revealed: bool

    @property
    def score(self) -> int:
        """Full marks, less whatever help was taken. Zero until it passes."""
        if not self.passed:
            return 0
        earned = FULL_MARKS
        if self.revealed:
            earned -= REVEAL_COST
        elif self.hinted:
            earned -= HINT_COST
        return max(earned, 0)


def record(exercise: str, *, passed: bool) -> None:
    """Note an attempt. Called by `check`; you should not need this yourself."""
    with _connect() as connection:
        connection.execute(
            "insert into attempts (exercise, passed, attempts) values (?, ?, 1) "
            "on conflict(exercise) do update set "
            " attempts = attempts.attempts + 1,"
            " passed = max(attempts.passed, excluded.passed),"
            " last_seen = datetime('now')",
            (exercise, int(passed)),
        )


def _mark(exercise: str, column: str) -> None:
    with _connect() as connection:
        connection.execute(
            f"insert into attempts (exercise, {column}) values (?, 1) "
            f"on conflict(exercise) do update set {column} = 1, last_seen = datetime('now')",
            (exercise,),
        )


def attempt(exercise: str) -> Attempt:
    with _connect() as connection:
        row = connection.execute(
            "select passed, attempts, hinted, revealed from attempts where exercise = ?",
            (exercise,),
        ).fetchone()
    if row is None:
        return Attempt(exercise, passed=False, attempts=0, hinted=False, revealed=False)
    return Attempt(exercise, bool(row[0]), int(row[1]), bool(row[2]), bool(row[3]))


def all_attempts() -> list[Attempt]:
    with _connect() as connection:
        rows = connection.execute(
            "select exercise, passed, attempts, hinted, revealed from attempts order by exercise"
        ).fetchall()
    return [Attempt(r[0], bool(r[1]), int(r[2]), bool(r[3]), bool(r[4])) for r in rows]


def hint(exercise: str, *, reveal: bool = False) -> bool:
    """Print the next level of help, and record that it was taken.

    Returns True when something was printed. The cost is applied once: asking
    twice does not charge twice, because re-reading a hint you already paid for
    should never be discouraged.
    """
    from bootcamp_agent.checks import CHECKS, UnknownCheck

    if exercise not in CHECKS:
        raise UnknownCheck(f"no exercise {exercise!r}; known: {sorted(CHECKS)}")

    text = (HINTS.get(exercise) or {}).get("reveal" if reveal else "hint")
    if not text:
        where = "reveal" if reveal else "hint"
        print(
            f"no {where} written for {exercise} yet. The ❌ line from check() names the fix, "
            "and the worked answer is in this chapter's solutions/notebook.ipynb"
        )
        return False

    current = attempt(exercise)
    already = current.revealed if reveal else current.hinted
    _mark(exercise, "revealed" if reveal else "hinted")

    cost = REVEAL_COST if reveal else HINT_COST
    banner = "answer" if reveal else "hint"
    price = "already taken, no further cost" if already else f"-{cost} XP"
    print(f"💡 {banner} for {exercise}  ({price})\n")
    print(text.strip())
    if not reveal:
        print(
            f"\nStill stuck? hint({exercise!r}, reveal=True) shows the answer (-{REVEAL_COST} XP)."
        )
    return True


#: Written per exercise, and deliberately not generated. A hint that does not
#: know which mistake you probably made is not a hint.
#:
#: Two tiers. `hint` is the nudge that gets an unstuck person moving; `reveal`
#: is the worked answer AND the reason, because an answer without the reason
#: teaches the next exercise nothing.
HINTS: dict[str, dict[str, str]] = {
    "w01-e2": {
        "hint": (
            "Think about what `Path('/').parent` returns. It is not an error, and it is not "
            "None. Print it and the loop's problem becomes obvious."
        ),
        "reveal": (
            "    while not (here / 'pyproject.toml').exists() and here != here.parent:\n"
            "        here = here.parent\n\n"
            "`Path('/').parent` is `Path('/')` again, so a loop that only checks for the file "
            "climbs past the root forever. Comparing a directory with its own parent is the "
            "only stopping condition that cannot run away, and you will see this idiom in "
            "every notebook in this course."
        ),
    },
    "w03-e1": {
        "hint": (
            "The default `[]` is written once, in the `def` line. How many times does Python "
            "execute that line? Not once per call."
        ),
        "reveal": (
            "    def add_tag(tag, tags=None):\n"
            "        if tags is None:\n"
            "            tags = []\n"
            "        tags.append(tag)\n"
            "        return tags\n\n"
            "A default argument is evaluated once, when the function is defined, so a bare "
            "`[]` is a single list shared by every call for the life of the process. `None` "
            "is immutable and cannot be shared, so building the list inside gives each call "
            "its own."
        ),
    },
    "w04-e1": {
        "hint": (
            "You need three things in the URL: the endpoint that means 'today', the currency "
            "you are starting from, and a filter so you get one rate back instead of thirty."
        ),
        "reveal": (
            "    https://api.frankfurter.dev/v1/latest?base=USD&symbols=BRL\n\n"
            "`/v1/latest` is today's rate; a date in the path is the historical endpoint. "
            "`base` is what you hold, `symbols` is what you want it in. Without `symbols` the "
            "response carries every currency the ECB publishes, and you pay for all of them "
            "in bytes, latency and attention."
        ),
    },
    "w04-e3": {
        "hint": (
            "Ask who is harmed. A public read endpoint answering without a key costs its "
            "owner some rate limiting. Does it expose anything that was meant to be private?"
        ),
        "reveal": (
            "It is not a vulnerability. Keys on an API like this buy a rate tier, not entry, "
            "and a public read endpoint answering publicly is the product working.\n\n"
            "What it is: a specification describing something the endpoint does not enforce. "
            "An agent reading only the spec concludes it needs a key it does not have, and "
            "either refuses to call or invents an Authorization header. A working endpoint "
            "looks closed to it. One request with no key settled the question in less time "
            "than reading the security section took."
        ),
    },
    "w05-e1": {
        "hint": (
            "Run `help(textwrap.fill)` and look only at the first line. It reads "
            "`fill(text, width=70, **kwargs)`. Which name comes first inside the brackets?"
        ),
        "reveal": (
            "    answer = ('fill', 'text')\n\n"
            "The signature line help() prints lists parameters in the order the function "
            "takes them, and `text` is first. `width` is second and has a default, which is "
            "why you can call `fill(paragraph)` without it. The checker asks "
            "`inspect.signature` the same question, so any public textwrap function works "
            "as long as the second item is really its first parameter."
        ),
    },
    "w05-e2": {
        "hint": (
            "Fix them in the order ruff lists them: move the import to the top, one space "
            "after every `#`, no space before a `:`, spaces around `=`, two blank lines "
            "around the function, and indent the body by four."
        ),
        "reveal": (
            "    # Import the package we need\n"
            "    import statistics\n\n"
            "    # Define our data\n"
            "    my_dict = {'a': 10, 'b': 3, 'c': 4, 'd': 7}\n\n\n"
            "    # Helper function\n"
            "    def dict_to_list(d):\n"
            '        """Convert dictionary values to a list"""\n'
            "        # Extract values and convert\n"
            "        x = list(d.values())\n"
            "        return x\n\n\n"
            "    print(dict_to_list(my_dict))\n"
            "    print(statistics.mean(dict_to_list(my_dict)))\n\n"
            "Every change is whitespace or a comment. The output is byte for byte the same, "
            "and the checker runs the file to prove it: style is for the reader, never for "
            "the interpreter."
        ),
    },
    "w05-e3": {
        "hint": (
            "Look at the shape of each line, not the words. `import X` brings in a package. "
            "`Capitalised(...)` builds an instance. `something.name(...)` calls a method on "
            "`something`, and a string literal is a something too."
        ),
        "reveal": (
            "    labels = {\n"
            "        'import collections': 'package',\n"
            "        'collections.Counter(words)': 'class',\n"
            "        'counts.most_common(2)': 'method',\n"
            "        \"' '.join(words)\": 'method',\n"
            "    }\n\n"
            "The one people miss is the last. `' '` is a `str` instance, so `.join` is a "
            "method call on it, the same shape as `counts.most_common(2)`. Modularity is "
            "these three shapes and nothing else: a package you import, a class you "
            "instantiate, a method you call on the instance."
        ),
    },
    "w06-e1": {
        "hint": (
            "Only one operator names a single version. `>=` says 'this or anything newer', "
            "and a bare name says 'anything'. Both of those float."
        ),
        "reveal": (
            "    table = {\n"
            "        'requires': ['matplotlib', 'numpy==1.15.4', 'pycodestyle>=2.4.0'],\n"
            "        'exact': ['numpy'],\n"
            "        'floating': ['matplotlib', 'pycodestyle'],\n"
            "    }\n\n"
            "`==` is the only exact pin. `>=2.4.0` accepts 2.4.0, 2.9 and 4.0, so two machines "
            "can resolve it differently on different days; that is what a lockfile such as "
            "`uv.lock` exists to prevent. The checker parses the strings the way an installer "
            "would, so the answer must match the specifiers, not the lesson."
        ),
    },
    "w06-e2": {
        "hint": (
            "The function lives in `my_package/utils.py`. For `my_package.we_need_to_talk` to "
            "exist, `__init__.py` has to import it from the sibling module, and a sibling "
            "import starts with a dot."
        ),
        "reveal": (
            "    INIT_LINE = 'from .utils import we_need_to_talk\\n'\n\n"
            "`__init__.py` runs when the package is imported, and whatever it imports becomes "
            "an attribute of the package. `.utils` is a relative import: 'the utils module "
            "next to me'. The checker imports the package in a fresh interpreter and confirms "
            "`my_package.we_need_to_talk` is the same object as `my_package.utils."
            "we_need_to_talk`, so copying the function into __init__.py does not pass."
        ),
    },
    "w06-e3": {
        "hint": (
            "The cell already writes the docstring for you; it just has nothing in it. Write "
            "the sentence a user needs before they open the source: what is the package for?"
        ),
        "reveal": (
            "    PACKAGE_DOC = 'Tools for talking to a partner.\\n\\nOne function, two "
            "moods.'\n\n"
            "A docstring is the first statement in a file, and for a package that file is "
            "`__init__.py`. `help()` prints its first line beside NAME and the rest under "
            "DESCRIPTION. The checker renders `help(my_package)` in a fresh interpreter and "
            "looks for your first line in it; any real sentence passes, a placeholder does not."
        ),
    },
    "w07-e1": {
        "hint": (
            "Read the docstring: `:ivar attribute:`. The instance variable it promises is "
            "called `attribute`, so that is the name __init__ must assign to."
        ),
        "reveal": (
            "    def __init__(self, value):\n"
            "        self.attribute = value\n\n"
            "`self` is the instance being built, and `self.attribute = value` stores the "
            "parameter on it under the documented name. The parameter is called `value` and "
            "the attribute is called `attribute`; they do not have to match, and the "
            "docstring is the contract that says which is which."
        ),
    },
    "w07-e2": {
        "hint": (
            "Defining __init__ on the child REPLACES the parent's __init__. Nothing runs the "
            "parent's unless the child calls it, and the call goes first."
        ),
        "reveal": (
            "    class ChildClass(ParentClass):\n"
            "        def __init__(self):\n"
            "            ParentClass.__init__(self)\n"
            "            self.child_attribute = 'I am a child class attribute!'\n\n"
            "`super().__init__()` is the same call without naming the parent, and the next "
            "exercise uses it. Either way the parent's __init__ runs on this instance and "
            "sets `parent_attribute`; the checker builds a child and looks for every "
            "attribute the parent alone would have set."
        ),
    },
    "w07-e3": {
        "hint": (
            "`Parent.__init__()` is a call with no instance. Read the TypeError: it names "
            "the argument that is missing."
        ),
        "reveal": (
            "    class SuperChild(Parent):\n"
            "        def __init__(self):\n"
            "            super().__init__()\n"
            '            print("I\'m a super child!")\n\n'
            "`super().__init__()` passes `self` for you and finds the next class up the MRO. "
            "Each level calls up before printing, so building a Grandchild prints the parent "
            "line, then the super child line, then its own: the checker compares that order "
            "with what each ancestor prints on its own."
        ),
    },
    "w07-e4": {
        "hint": (
            "Two changes. The method's name gains a leading underscore, and __init__ calls "
            "it: `self.tokens = self._tokenize()`."
        ),
        "reveal": (
            "    class Document:\n"
            "        def __init__(self, text):\n"
            "            self.text = text\n"
            "            self.tokens = self._tokenize()\n\n"
            "        def _tokenize(self):\n"
            "            return tokenize(self.text)\n\n"
            "The underscore is a convention, not a lock: Python will still let a caller run "
            "`doc._tokenize()`. It tells the reader the method is an internal step, may "
            "change without notice, and is not the way to get tokens. `doc.tokens`, set once "
            "in __init__, is the public promise."
        ),
    },
    "w08-e1": {
        "hint": (
            "doctest is telling you the truth: the example says 9, the body returns 27. "
            "The function is called square. Which of the two is wrong?"
        ),
        "reveal": (
            "    def square(x):\n"
            '        """Square the number x\n\n'
            "        :param x: number to square\n"
            "        :return: x squared\n\n"
            "        >>> square(3)\n"
            "        9\n"
            '        """\n'
            "        return x * x\n\n"
            "The docstring example is a test, and `doctest` ran it. `x ** 3` is a cube, so "
            "the fix is the body, not the example; changing the example to 27 would make a "
            "function called square lie. The checker runs doctest itself and then calls "
            "square(3) and square(-2), so both the example and the arithmetic have to hold."
        ),
    },
    "w08-e2": {
        "hint": (
            "Read the assertion pytest prints: left is what the code produced, right is what "
            "the test claimed. One of them is missing a vowel."
        ),
        "reveal": (
            "    def test_document_tokens():\n"
            "        doc = Document('a e i o u')\n"
            "        assert doc.tokens == ['a', 'e', 'i', 'o', 'u']\n\n"
            "Five tokens in, five out; the test claimed four. A failing test is not always a "
            "bug in the code, and reading the diff is how you tell. The checker runs pytest "
            "on your file in a child process and wants exactly `2 passed`: the fixed test and "
            "the empty-document edge case, both green."
        ),
    },
    "w08-e3": {
        "hint": (
            "Name the things, not their types. What is `x`? A temperature. What is 100? "
            "The boiling point of water. What does True mean? That it is boiling."
        ),
        "reveal": (
            "    def is_boiling(temp, boiling_point=100):\n"
            "        return temp >= boiling_point\n\n"
            "    renamed = is_boiling\n\n"
            "`check(x, y=100)` forces every reader to work out what the comparison means. "
            "`is_boiling(temp, boiling_point=100)` says it. The other failure mode is "
            "`check_if_temperature_is_above_boiling_point(temperature_to_check, "
            "celsius_water_boiling_point=100)`: true, and unreadable. The checker rejects "
            "both ends and confirms the function still returns first >= second."
        ),
    },
    "w09-e1": {
        "hint": (
            "Two things are missing from convert_timezone, and both are the deck's step 3: "
            "a type hint on each of the three parameters and on the return value, and a "
            "docstring that names every argument. The check parses the file, so the "
            "docstring has to be the first statement in the function body."
        ),
        "reveal": (
            "    @mcp.tool()\n"
            "    def convert_timezone(date_time: str, from_timezone: str, to_timezone: str) "
            "-> str:\n"
            '        """\n'
            "        Convert a datetime from one timezone to another.\n\n"
            "        Args:\n"
            "            date_time: The datetime string in ISO format (e.g., "
            "'2025-01-20T14:30:00')\n"
            "            from_timezone: Source timezone (e.g., 'America/New_York')\n"
            "            to_timezone: Target timezone (e.g., 'Europe/London')\n\n"
            "        Returns:\n"
            "            A string with the converted datetime and timezone information\n"
            '        """\n\n'
            "The hints become the tool's input schema and the docstring becomes its "
            "description. Together they are everything a client or a model knows about the "
            "tool before calling it, which is why the check refuses a docstring that skips "
            "an argument."
        ),
    },
    "w09-e2": {
        "hint": (
            "Where does the child process start? In the notebook's directory, which is not "
            "where the server file was written. Look at what StdioServerParameters is given "
            "as args, and at the value of server_path."
        ),
        "reveal": (
            "    params = StdioServerParameters(command=sys.executable, "
            "args=[str(server_path)])\n\n"
            "The server is a child process, started wherever the client is. A relative "
            "'timezone_server.py' is looked up there, the interpreter exits at once, and the "
            "client reports 'Connection closed'. The absolute path fixes it. sys.executable "
            "matters for the same reason: the child needs the interpreter that has mcp "
            "installed, not whatever 'python' is on the PATH."
        ),
    },
    "w09-e3": {
        "hint": (
            "The server told you what was wrong: three fields are required and none of the "
            "keys you sent is one of them. Print tools[0].input_schema['properties'] and use "
            "those names."
        ),
        "reveal": (
            "    arguments = {\n"
            '        "date_time": "2025-01-20T14:30:00",\n'
            '        "from_timezone": "America/New_York",\n'
            '        "to_timezone": "Asia/Tokyo",\n'
            "    }\n\n"
            "The argument names are the parameter names of the function on the server, and "
            "the client sees them as the input schema's properties. A guessed key is a "
            "validation error, and the server sends it back as a result with is_error set "
            "rather than as an exception, so the loop that made the call can read it. The "
            "check computes the expected time with zoneinfo: 14:30 in New York is 04:30 the "
            "next day in Tokyo."
        ),
    },
    "w10-e1": {
        "hint": (
            "The resource works and the client reads it. Look at what it joins the zones "
            "with, and then at what a reader has to do to get a list back out of that text."
        ),
        "reveal": (
            '    @mcp.resource("file://locations.txt")\n'
            "    def get_locations() -> str:\n"
            '        """Every timezone this server can convert, one per line."""\n'
            '        return "\\n".join(sorted(ZONES))\n\n'
            "A resource is read-only context, and context is read by something else. One "
            "zone per line splits on a newline; the same twelve zones joined by commas is "
            "one string that every reader has to parse before it can use it. The check "
            "compares the text the client received against the fixture's sorted keys, so "
            "it is judging the wire, not your source."
        ),
    },
    "w10-e2": {
        "hint": (
            "The client printed both: the server lists one name, and you asked for another. "
            "The title went to the decorator. The name is the function you decorated."
        ),
        "reveal": (
            '    PROMPT_NAME = "convert_timezone_prompt"\n\n'
            '@mcp.prompt(title="Timezone Conversion") sets a title for people to read in '
            "a client's menu. The prompt's name is the decorated function's name, which is "
            "what list_prompts() reports and what get_prompt() wants. Asking for the title "
            "gets you nothing back at all. The check refuses a name equal to the title for "
            "exactly that reason, and it refuses rendered text that does not contain the "
            "request verbatim: the template's whole job is to wrap what the person asked."
        ),
    },
    "w10-e3": {
        "hint": (
            "Count the model calls in the trace. There are two in the deck's workflow, and "
            "the second one is where the answer comes from. What does the follow-up message "
            "contain? Compare it with the 'tool_result' step you can see in the trace."
        ),
        "reveal": (
            '    followup = f"{message}\\n\\nTool result: {tool_text}"\n\n'
            "Step four is the whole reason the loop has five steps: the tool answered, and "
            "the model has not seen it yet. Send the query alone and the model decides to "
            "call the tool again, because from where it sits nothing has happened. The "
            "check reads the last step's detail and looks for the converted time, so a "
            "five-step trace with an answer that never names 09:50:00+00:00 still fails."
        ),
    },
    "w10-e4": {
        "hint": (
            "Read the answer the loop gave: it converted something. Then read the router's "
            "country branch and see what it does when it has nothing to offer. Where would "
            "the list of zones this server supports come from?"
        ),
        "reveal": (
            "    CANADA_CONTEXT = LOCATIONS_TEXT\n\n"
            "The resource is the read-only context, and this is what it is for. Without it "
            "the router knows a country was named and knows nothing about which zones exist "
            "here, so it picks one and converts, which reads like an answer and is a guess. "
            "With it the router offers the three Canadian zones in the table and asks which "
            "one. The check refuses any clock time in this answer and wants at least two "
            "zones named, because a clarifying question that offers no choices is just a "
            "refusal. This needs exercise 1's resource: one zone per line, or there is "
            "nothing to split."
        ),
    },
    "w11-e1": {
        "hint": (
            "The query already has the shape of the answer in it. Look at what surrounds "
            "{prefix} in the f-string: two quotes, and the caller controls the text between "
            "them. Where does a quote go if it comes from outside?"
        ),
        "reveal": (
            '    sql = "SELECT timezone FROM locations WHERE timezone LIKE ? LIMIT 50"\n'
            '    rows = conn.execute(sql, (f"%{prefix}%",)).fetchall()\n\n'
            "The ? is a placeholder the database fills in itself, after it has finished "
            "parsing the statement, so the value can never become SQL. Two lines change: the "
            "query loses its f, and execute() gains a tuple. Note that the wildcards stay in "
            "the VALUE, not in the query: '%' + prefix + '%' is what you are matching, and it "
            "is data. The checker parses your file and refuses an f-string, a %, a .format() "
            "or a concatenation anywhere near a SELECT, then runs the tool twice: 'Europe' has "
            "to still answer four zones, and the injection has to answer nothing."
        ),
    },
    "w11-e2": {
        "hint": (
            "Read the line the client printed: 'the schema wants'. Four names, and one of "
            "them is a secret. Anything in the signature is in the schema, and the schema is "
            "published. Where can the tool get the key without being handed it?"
        ),
        "reveal": (
            "    def convert_timezone(date_time: str, from_timezone: str, to_timezone: str) "
            "-> str:\n"
            '        headers = {"Content-Type": "application/json"}\n'
            '        api_key = os.environ.get("TIMEZONE_API_KEY")\n'
            "        if api_key:\n"
            '            headers["Authorization"] = f"Bearer {api_key}"\n'
            "        ...\n"
            '        return f"Time in {to_timezone}: {converted}"\n\n'
            "Three edits, and each closes a different leak. The signature: a parameter is "
            "schema, and schema is public. The read: os.environ at call time keeps the key in "
            "the process and out of the repository. The return: a tool result travels to the "
            "client and into the model's context, which is a transcript somebody will paste "
            "somewhere. `if api_key:` matters too, because a missing credential is a header "
            "you leave off rather than a crash. The checker parses all four of those rules "
            "and then calls the tool with no key in its environment, which is what a stdio "
            "child gets by default."
        ),
    },
    "w11-e3": {
        "hint": (
            "There is no wrong answer to the first two, only an unwritten one. The third has "
            "a number in it, and the cell above printed that number."
        ),
        "reveal": (
            "    ANSWERS = {\n"
            '        "trust": "The people teaching this course run it and session 13 '
            "uses it in class, so I can ask them what a tool does before I let a model "
            'call one.",\n'
            '        "security": "Its own instructions say it holds no key and hands back '
            "unsigned bytes for me to sign elsewhere, and I would still send it nothing I "
            'would not publish.",\n'
            '        "surface_area": "The recorded list holds 16 tools and a model with all '
            "of them in context can choose any one, so I would rather it saw the two I need "
            'than the whole set.",\n'
            "    }\n\n"
            "Your words, not these. What the check insists on is that the third answer names "
            "the number: sixteen tools is the surface area, and a judgement about surface "
            "area that does not say how large the surface is has not been made yet. It also "
            "refuses a paragraph, because a sentence you cannot say out loud is a decision "
            "you have not taken. The number comes from a RECORDED list, which is why the "
            "fixture says so in its own provenance note."
        ),
    },
    "w12-e1": {
        "hint": (
            "What is inside the lambda that timeit runs? Building a 60,000-entry dict is "
            "work, and it is being done on every repetition. The lookup is the only line "
            "that belongs in there."
        ),
        "reveal": (
            "    index = {doc_id: position for position, doc_id in enumerate(doc_ids)}\n"
            "    dict_ms = min(timeit.repeat(lambda: index[target], number=20, repeat=5)) "
            "/ 20 * 1000\n\n"
            "The dict is built once, outside the timed statement, and the statement is the "
            "lookup alone. min() of the repeats is the honest figure: every other run was "
            "the same code plus noise. The checker refuses a dict_ms that is not at least "
            "ten times smaller than linear_ms, because over 60,000 ids a real lookup is "
            "thousands of times faster, and a number that is not is a measurement of "
            "something else."
        ),
    },
    "w12-e2": {
        "hint": (
            "A set keeps one of each, and forgets the order it saw them in. A dict keeps one "
            "of each key too, and since Python 3.7 it remembers the order. Which one has a "
            "`fromkeys`?"
        ),
        "reveal": (
            "    def dedupe(citations):\n"
            "        return list(dict.fromkeys(citations))\n\n"
            "dict.fromkeys(citations) makes a dict with one key per distinct citation, in "
            "the order each was first seen; list() of it drops the None values. The other "
            "shape is a seen-set beside a list: append when the id is not in seen, then add "
            "it. The checker runs your function on two lists whose first-seen orders differ, "
            "so a set, which iterates in one hash-determined order, cannot pass both."
        ),
    },
    "w12-e3": {
        "hint": (
            "Where is the budget checked? Nowhere: the function visits, then recurses, then "
            "visits. Compare len(visited) with budget BEFORE appending, and return when the "
            "budget is spent. On a node whose children contain itself, that check is the "
            "only thing that ends the walk."
        ),
        "reveal": (
            "    def walk(node, budget, visited=None):\n"
            "        visited = [] if visited is None else visited\n"
            "        if len(visited) >= budget:\n"
            "            return visited\n"
            "        visited.append(node['name'])\n"
            "        for child in node['children']:\n"
            "            walk(child, budget, visited)\n"
            "        return visited\n\n"
            "The stopping condition comes first, before the work, which is what the "
            "loop-engineering guide asks of every loop. The checker runs your walk on a "
            "node that lists itself as its own child, under a five-second deadline: without "
            "the check the interpreter stops it with RecursionError, or never, and either "
            "one fails. With a budget of 5 it returns five names and stops."
        ),
    },
    "w12-e4": {
        "hint": (
            "Count the incoming edges of every node. The ones with zero are ready: nothing "
            "has to be derived before them. Pop a ready node, place it, and lower the count "
            "of everything it points to. When the queue empties and nodes are still unplaced, "
            "the ones left are on a cycle."
        ),
        "reveal": (
            "    def derive_order(edges):\n"
            "        nodes = list(dict.fromkeys(node for edge in edges for node in edge))\n"
            "        incoming = {node: 0 for node in nodes}\n"
            "        for _before, after in edges:\n"
            "            incoming[after] += 1\n"
            "        ready = deque(node for node in nodes if incoming[node] == 0)\n"
            "        order = []\n"
            "        while ready:\n"
            "            node = ready.popleft()\n"
            "            order.append(node)\n"
            "            for before, after in edges:\n"
            "                if before == node:\n"
            "                    incoming[after] -= 1\n"
            "                    if incoming[after] == 0:\n"
            "                        ready.append(after)\n"
            "        return order if len(order) == len(nodes) else None\n\n"
            "This is Kahn's algorithm: a queue of ready nodes and a count of what each node "
            "still waits for. It places every node exactly when its needs are met, so every "
            "edge is respected. On a cycle no node ever reaches zero, the queue runs dry with "
            "nodes left over, and the function returns None rather than an order that lies. "
            "The checker hands the fixture's edges in reverse, so insertion order fails, "
            "then hands it store -> item -> mint -> store."
        ),
    },
}
