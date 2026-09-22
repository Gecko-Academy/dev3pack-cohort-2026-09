---
name: <!-- write this: a short kebab-case name -->
description: <!-- write this: one line an assistant reads to decide whether to load this skill -->
---

# Skill

**Filled by:** session 10. The five sections are the ones `ch10-e1` reads, and
the evidence below is the before-and-after pair of runs you saved.

## When to use (`when_to_use`)

<!-- write this: the requests this skill is for, and the ones it is not for. -->

## Workflow (`workflow`)

<!-- write this: the steps, in order, that the assistant follows. -->

## Output format (`output_format`)

<!-- write this: the exact shape of what comes back, e.g. the ResearchAnswer
fields and what each one must hold. -->

## Failure rules (`failure_rules`)

<!-- write this: what to do when retrieval is empty, a citation does not
check, or the model does not answer. -->

## Safety boundary (`safety_boundary`)

<!-- write this: what the skill never does: no instruction taken from
retrieved text, no secret read, no write action. -->

## Evidence

### Without the skill (`without_skill`)

```text
<!-- paste this: an excerpt from the saved run without the skill -->
```

### With the skill (`with_skill`)

```text
<!-- paste this: an excerpt from the saved run with the skill -->
```

### The instruction you fixed (`improved_instruction`)

<!-- write this: the line you changed after seeing a failure, and why. -->
