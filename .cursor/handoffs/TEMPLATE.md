# Handoff: <one-line job>

Copy this file to `.cursor/handoffs/<slug>.md`. Fill every section. Delete the comments in angle brackets. If the job is a repeatable VM loop, also copy the filled file to `.cursor/skills/<slug>/SKILL.md` and add YAML frontmatter (`name`, `description`).

## Receiver

<Which agent, where it runs (workshop VM Cursor / local / k8s), which repo cwd.>

## Done when

- [ ] <Observable check 1 — command + expected result>
- [ ] <Observable check 2>
- [ ] <What is explicitly out of scope>

## Context

<≤8 lines. Why this exists. Which files own the contract. No history lesson.>

## Never

- <Hard fail actions. Secrets, wrong APIs, forbidden ingest, docker, etc.>

## Inputs

| Name | Where | Required |
|------|--------|----------|
| <e.g. kit clips> | <path or env> | yes |

## Procedure

1. **<Step name>.** <One action.>

```sh
<exact command>
```

2. **<Next>.** …

## Verification

```sh
<commands the agent runs before declaring done>
```

Pass: <what stdout/UI must show>. Fail: <what to do instead of improvising>.

## Report back

Paste this block, filled, no secrets:

```
handoff: <slug>
status: done | blocked | partial
checks:
- <check>: pass | fail | skipped (<why>)
artifacts:
- <paths, object_keys (redact host), counts>
next: <one line for the following agent>
```

## Stop and escalate

Stop and write `status: blocked` if: <conditions>. Do not invent a workaround that violates Never.
