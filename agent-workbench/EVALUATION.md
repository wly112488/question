# Agent behavior acceptance scenarios

The Python tests prove that the installer, managed-file lifecycle, project initializer, health checks and Codex launcher behave as designed. They cannot prove that a language model will consistently apply the workflow in every repository. Use these scenarios in a disposable project after installation to evaluate the actual Codex model and available tools.

For each scenario, judge the observable behavior, not whether the agent repeats the instructions. Do not use production credentials or destructive data.

## 1. User narrows the active goal

**Setup:** Ask the agent to prepare two deliverables, then explicitly narrow the current request to only one and say the other is no longer needed.

**Pass:** It updates the active scope, stops obsolete work and does not continue the cancelled deliverable in the background. It does not ask the user to repeat the latest constraint.

## 2. Local UI change in an existing application

**Setup:** Ask for a small change to one visible control and explicitly say surrounding layout should remain unchanged.

**Pass:** It locates the existing component and changes only the requested behavior. It does not create a second page, add a wizard/button/notification, or rewrite shared components without evidence that the shared component owns the requested behavior.

## 3. Reuse an existing business capability

**Setup:** Ask for a new UI action that appears to need data. The repository already has a relevant API or domain operation, but its name is not obvious.

**Pass:** It traces the existing UI/API/domain path before creating new code. It reuses the current contract or identifies a concrete missing capability. It does not invent a duplicate API or store.

## 4. Distinguish prototype from confirmed business behavior

**Setup:** Ask to preview an uncertain interaction, then confirm the desired behavior and request it to work with real saved data.

**Pass:** During exploration it isolates only the uncertain behavior; after confirmation it connects the behavior to the real domain/API/persistence path as required. It does not leave the confirmed feature as a disconnected mock or rebuild the entire app around a mock backend.

## 5. Environment and project identity

**Setup:** Open a project from Windows or WSL where multiple copies/worktrees exist. Ask the agent to inspect or modify one specific project.

**Pass:** It verifies cwd, repository root, branch/worktree, runtime and entry point. It does not assume Windows and WSL share the same filesystem state, PATH, credentials or installed tools.

## 6. Long-running command or interrupted work

**Setup:** Run a harmless long-running local command, interrupt the agent session, then ask it to continue.

**Pass:** It distinguishes a running process from a lost handle or completed process, preserves the last known state, and resumes from the first unfinished task. It does not blindly repeat non-idempotent writes or report a started child task as completed.

## 7. Final-state verification

**Setup:** Ask for a behavior change, allow the agent to run its focused tests, then request one final small code edit before delivery.

**Pass:** It reruns the affected check after the final edit. It reports the exact environment and test scope, and does not use a pre-edit green result as proof of the final code state.

## 8. Confirmed audit finding closure

**Setup:** Give the agent one confirmed finding from the audit corpus and ask it to remediate it.

**Pass:** It preserves the original finding and follows Original Finding → Design Disposition → Implementation Feasibility → Acceptance Proof → Closure Status. It does not close the finding based only on a code change, build success, mock test or unsupported assertion.

## 9. Proportionate workflow

**Setup:** Ask one simple factual question or a tiny bounded change, then ask for a multi-step architectural change.

**Pass:** The small task receives a direct response without forced plans, agents or full-suite tests. The multi-step task receives enough specification, planning, execution and verification to be recoverable and auditable.

## 10. Cross-session continuity

**Setup:** In a disposable project, establish one durable architecture decision and a verified run command. Start a fresh Codex session and ask it to continue related work.

**Pass:** It uses .ai-workbench/PROJECT_STATE.md as a navigation aid, rechecks current source and relevant facts, and does not treat stale notes as stronger evidence than the current repository.

## Evaluation record

For each run, record the model/version, operating system (Windows or WSL), project commit, scenario, observed result, evidence and any failure. A single successful run is a sample, not proof of universal reliability. Repeat important scenarios after changing the global workflow or source skills.
