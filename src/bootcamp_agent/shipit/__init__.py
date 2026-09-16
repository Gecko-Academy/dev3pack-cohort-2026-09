"""The Ship It track: turn the capstone into a surface somebody else can call.

Everything here is offline and imports nothing outside the standard library.
That is not a style preference. The course declares exactly one runtime
dependency, and CI installs it frozen, so a track that imported the real Gecko
package would change the install on every learner's laptop -- which is the one
thing the assessed lane must never do.

The cost of that choice is a duplicated byte layout (:mod:`borsh_store`), and it
is paid for with a golden fixture rather than with discipline. See that module.
"""
