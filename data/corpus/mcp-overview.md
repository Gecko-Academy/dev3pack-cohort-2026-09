<!-- title: MCP Overview -->
<!-- tags: mcp, tools, protocol, integration, agents -->

# MCP Overview

The Model Context Protocol (MCP) is an open standard for connecting AI
applications to external capabilities. Where a tool is a function an agent can
call inside one application, an MCP server packages a set of tools, resources,
and prompts behind a protocol boundary so that any MCP-capable client — Claude
Code, Cursor, VS Code, a custom agent — can discover and use them without custom
integration code.

## The moving parts

An **MCP server** exposes capabilities: tools (functions with JSON-schema
signatures), resources (readable data), and prompts (reusable templates). An
**MCP client** is the agent-side application that connects to servers, lists
their capabilities, and routes the model's tool calls to the right server.
Transport is pluggable — stdio for local servers, HTTP for hosted ones. The
protocol's value is the decoupling: the server's author does not need to know
which assistant will call it.

## Tools vs skills vs MCP servers

These three are commonly confused. A **tool** is a callable capability with a
narrow contract — it executes. A **skill** is packaged instructions — a folder
of guidance the model loads to perform a workflow well; it does not execute
anything by itself. An **MCP server** is a distribution boundary for tools and
resources — it makes capabilities available across applications. A well-built
agent system often uses all three: an MCP server provides the tools, and a skill
teaches the model when and how to use them.

## Trust and safety at the boundary

Connecting an MCP server is granting capabilities, and the connection point is a
security boundary. Practical rules: prefer read-only servers while learning;
never place credentials in client configuration files that get committed;
treat everything a server returns as untrusted data, not instructions; and use
recorded or offline modes when they exist, so a misbehaving prompt cannot cause
a real side effect. A server that can spend money or mutate production state
deserves the same review as giving a new contractor production access.

## Why it matters for this course

MCP is how the capstone assistant stops being an island: the same assistant that
answers from a local corpus can, through one configuration entry, gain vetted
access to an external API surface — with the safety boundary made explicit
instead of implied.
