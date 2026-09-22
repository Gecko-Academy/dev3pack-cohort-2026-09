# Evaluation report

**Filled by:** session 7 (the baseline, and the evaluator's weakness), session 9
(failures named from traces), session 14 (one fix, measured after).

Every number below has the command that produced it, the commit it ran on, and
the model. A number without its command is an impression, and this file holds
none. CI has no keys, so any number CI printed is the offline fake model's.

## Before

- model: <!-- write this: fake, or the provider and model name from your .env -->
- commit: <!-- write this: `git rev-parse --short HEAD` when you ran it -->
- command: <!-- write this: the exact command, e.g. `uv run bootcamp capstone grade` -->
- result: <!-- paste this: the pass rate or score line it printed -->

### The evaluator's weakness (session 7)

<!-- write this: what the pass condition does not check. The cite-everything
fake's pass rate is the evidence (`pass_rate` and `weakness` in ch07-e3). -->

### Failures, named from traces (session 9)

| Case | Bucket | The trace line that decided it |
|---|---|---|
| <!-- write this --> | <!-- e.g. retrieval_miss, instruction_following --> | <!-- paste this: the line --> |

## After

The fix for rank 1 of [ISSUES.md](ISSUES.md) (session 14).

- model: <!-- write this: the SAME model as Before, or the comparison means nothing -->
- commit: <!-- write this -->
- command: <!-- write this: the same command as Before -->
- result: <!-- paste this -->
- regression test: <!-- write this: its name in tests/ -->

### What got better (session 7's `improvement`)

<!-- write this: one sentence naming what improved, and by how much. -->

### What got worse, or could (session 7's `regression_or_risk`)

<!-- write this: one sentence. "None" is almost never true. -->
