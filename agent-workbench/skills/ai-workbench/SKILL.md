---
name: ai-workbench
description: Use for software work that needs repository understanding, architecture or implementation decisions, debugging, refactoring, cross-session continuity, tool selection, or end-to-end delivery. Also use when recurring workflow failures suggest a systemic fix.
---

# AI Workbench: evidence-driven delivery

Origin: [historical audit and solution design](https://github.com/wly112488/question/blob/main/PROPOSED_SOLUTION_DESIGN.md). The original audit records remain evidence; this skill is the runtime execution translation, not a claim that historical findings are closed.

Use this skill to translate the historical audit's six mechanisms into proportionate execution. The current user request and project specifications remain authoritative; this skill does not authorize scope expansion or override a project contract.

## 1. Establish the active truth

Before acting, identify the user's current outcome, latest constraints, target repository/worktree/branch, current working directory, actual runtime and entry point. Treat newer user instructions as superseding older scope. Stop work that no longer serves the active goal.

Keep these evidence classes separate:
- **Confirmed intent:** explicit user decision or approved specification.
- **Observed implementation:** facts read from current source/configuration.
- **Verified outcome:** behavior observed in the current environment and code state.
- **Hypothesis:** plausible explanation not yet proven.
- **Unknown:** evidence not available.

Do not convert assumptions into requirements or tests-before-change into proof-after-change.

## 2. Locate before creating

For an existing behavior, trace the shortest relevant path from its visible entry point to the owning component/module, state, event, API, domain rule and persistence. Search for symbols and read small local ranges first; expand only for a concrete missing dependency. Inspect runtime evidence when source alone cannot establish what the user sees.

Reuse existing components, contracts, tools, data and environment capabilities. A failed search is not proof that a capability does not exist. Do not create a second component, API, data store, service or toolchain until the existing path has been checked and a concrete gap is established.

For UI work, distinguish a local visual adjustment from a behavior change, shared-component change, data change or workflow change. Preserve surrounding areas the user did not ask to change. Do not add wizards, steps, buttons, notifications or new abstractions merely because they seem orderly.

## 3. Choose implementation depth

- Visual exploration: make the smallest real, operable change in the existing UI; avoid building a parallel prototype when the current project can preview the change.
- Existing backend capability: reuse the real API and data path.
- Unsettled behavior not supported by current contracts: isolate only the uncertain behavior in a clearly identified preview adapter or fixture; do not copy the whole application or silently write preview data into production storage.
- Confirmed business behavior: implement through the real domain/API/persistence path when required by the requested outcome. Do not leave a confirmed rule as a disconnected mock.
- Refactoring: preserve approved behavior and existing coverage; refactor only where evidence shows the structure obstructs the required outcome.

Do not invent business semantics. If a decision materially changes data meaning, ownership, authorization, irreversible behavior or acceptance, ask one focused question after resolving everything repository evidence can answer.

## 4. Execute proportionately

For a small bounded change, proceed directly. For work with multiple dependent tasks, meaningful architecture decisions or a long horizon, use the installed writing-specs/writing-plans and executing-plans skills as applicable. The plan is not a substitute for inspecting current source; revise mechanics when implementation evidence changes, without silently changing spec semantics.

For behavior-changing production code, follow the installed test-driven-development skill: RED, verify the expected failure, GREEN, verify, then refactor. For behavior-preserving refactoring, establish sufficient green coverage first and keep it green. Follow task-execution-discipline for plan tasks.

Keep one primary agent responsible for the whole outcome. Delegate only genuinely independent investigation or review with explicit inputs/outputs. Parallel workers require isolated worktrees; integrate and verify their results before claiming completion.

## 5. Role model and interaction boundary

One primary **Driver** owns the goal, current scope, architecture decisions, integration and final claim. The Driver may switch responsibility modes without spawning agents:
- **Investigator:** gathers the smallest sufficient source/runtime evidence and records unknowns.
- **Architect:** chooses the smallest coherent design that preserves confirmed product behavior and existing assets.
- **Builder:** makes the change and keeps it within the approved scope.
- **Verifier:** checks the final changed state against the original user task and acceptance evidence.

These are responsibility boundaries, not mandatory separate agents or approval gates. Spawn a subagent only when a bounded investigation or implementation is genuinely independent, its result can be integrated safely, and expected benefit exceeds handoff/coordination cost. The Driver remains accountable.

User interaction should stay lightweight: show a useful result or concise decision point at meaningful milestones; do not ask the user to manage tools, shell environments, components, API names, test commands or agent assignments. Ask only for a material business choice, missing authority/credentials or an access boundary that cannot be resolved from evidence.

## 6. Manage execution and recovery

Use the actual shell, interpreter, PATH, cwd and worktree. Windows, WSL and child shells are distinct environments; verify the environment where the command will run. Discover existing browsers, runtimes and helpers before installing new ones.

For long operations, distinguish running, no-output progress, authorization wait, service readiness, network wait, blocked stdin/EOF, lost handle and actual hang. Use bounded waits and checkpoints. Retry only after diagnosing the failure and confirming the operation is safe/idempotent. Preserve durable partial work and resume from the first unfinished requirement rather than restarting blindly.

For external writes or uploads, retain a checkpoint/revision and verify the resulting object. A successful command exit, HTTP response or API acknowledgement is not automatically proof of the final user-visible state.

## 7. Verify the final state

Choose checks based on changed behavior and risk. Small visual changes need focused checks; data, permission, persistence, cross-page state, deployment and shared contracts need correspondingly broader proof. Do not run unrelated full suites for reassurance, but never skip verification required by the plan or applicable source skill.

After the final code edit, rerun the directly affected checks. Bind evidence to the actual code state, environment, data/fixture, service instance and entry point. Distinguish static checks, build, mock behavior, real API behavior, persistence, browser rendering and end-to-end user tasks.

When a confirmed historical finding is claimed as remediated, use auditing-finding-closure: Original Finding → Design Disposition → Implementation Feasibility → Acceptance Proof → Closure Status. Do not weaken, defer, delete or reclassify it without explicit approval. TO_CONFIRM is not closure.

## 8. Preserve useful project state

For multi-step work or likely cross-session continuation, maintain .ai-workbench/PROJECT_STATE.md as a concise durable handoff: project entry points, confirmed decisions, verified commands and environment, active objective, unresolved unknowns and next recovery action. Update only when durable facts or the recovery point change. The repository, specs, commits, tests and persisted artifacts remain authoritative; this file is a navigation aid, not proof.

## 9. Completion report

State what changed, where, which exact checks ran, what user-visible or runtime behavior was verified, and what remains unverified or requires user action. Never report a preview as production behavior, a local build as deployment, or a test pass from an earlier code state as proof of the final state.
