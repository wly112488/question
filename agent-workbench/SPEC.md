# AI Workbench for Codex — Product Specification

**Status:** Approved for implementation by the user's request in this conversation.  
**Scope:** A deployable, cross-platform local workflow layer for Codex CLI.  
**Primary source material:** `../PROPOSED_SOLUTION_DESIGN.md`, `../README.md`, and the current `wly112488/ai-specs` repository.  
**Source revisions inspected:** question `e35c3c1a45e4db7ad3733a338ca385484d0c3e54`; ai-specs `9ca76943de343fb0935b9acd423b8d8874d541b2`.

## 1. Purpose

Provide one installable `aiw` command that makes the existing Codex CLI consistently apply the collaboration and execution mechanisms derived from the historical audit, from either Windows or WSL.

The product is an integration and policy layer around Codex CLI. It does not reimplement the model, shell, sandbox, authentication, or Codex execution engine. It installs managed global instructions and current skills, initializes a project with a small managed instruction section and durable project state, diagnoses installation health, updates from the authoritative private `ai-specs` repository, and launches the user's existing `codex` command in the selected project.

## 2. Source roles and authority

| Source | Role | Authority |
|---|---|---|
| `question/PROPOSED_SOLUTION_DESIGN.md` | Product goals, six mechanisms, 120-topic remediation map, collaboration insights | Product design input |
| `question/issue_descriptions` and `cause_annotations` | Historical evidence and finding context | Evidence; not runtime instructions |
| `ai-specs/RULE_MAINTENANCE_SPEC.md` | How execution specs are maintained | Normative for rule maintenance |
| `ai-specs/auditing-finding-closure` | Confirmed-finding closure lifecycle | Normative when remediating confirmed findings |
| `ai-specs/execution-specs/*` | Plan execution, TDD, task execution discipline | Normative when their triggers apply |
| `ai-specs/writing-plans`, `writing-specs` | Planning/specification workflow | Normative when their triggers apply |

The installer MUST clone or use a caller-supplied local checkout of the private `wly112488/ai-specs` repository. It MUST NOT silently vendor stale copies of those rules into the product repository. Installed skills are deployment copies; the private repository remains their source of truth. The installed manifest records the exact upstream commit.

Historical findings are not automatically declared fixed by installing this product. The runtime is intended to reduce recurrence and improve execution; historical finding closure still requires the original-finding proof contract.

## 3. Users and operating environments

- Windows 10/11 PowerShell or cmd with Python 3.10+ and Git.
- WSL2 Linux shell with Python 3.10+ and Git.
- Existing authenticated Codex CLI installation.
- Existing Git credentials that can read the private `ai-specs` repository, or an explicit local `--specs-dir`.

No third-party Python runtime dependencies are permitted.

## 4. User-visible workflow

### 4.1 Install

From a clone of `wly112488/question`:

Windows:
```powershell
py -3 .\agent-workbench\aiw.py install
```

WSL:
```bash
python3 agent-workbench/aiw.py install
```

The command:
1. locates Git and Codex;
2. clones or updates `ai-specs` into the platform's user data directory, unless `--specs-dir` is provided;
3. installs the managed global Codex instruction block;
4. installs selected current skills into `~/.agents/skills` (or the Windows home equivalent);
5. installs the `aiw` launcher in a user-level bin directory;
6. records source revision and content hashes in a manifest;
7. prints exact PATH or prerequisite actions still required.

### 4.2 Initialize a project

`aiw init [PROJECT_PATH]` adds a clearly delimited managed block to the project's root `AGENTS.md`, preserving all pre-existing content. It creates `.ai-workbench/PROJECT_STATE.md` and a small project config only when absent. Re-running init is idempotent.

### 4.3 Diagnose and update

- `aiw doctor`: offline health check for Python, Git, Codex, source checkout, managed instructions, skills, launcher, and current project.
- `aiw status`: show installed source revision and managed file state.
- `aiw update`: fast-forward the private specs checkout and safely refresh managed instructions/skills. User-modified managed content is never overwritten silently.
- `aiw uninstall`: remove only files/blocks that are still byte-identical to the tool's recorded managed versions. Preserve modified files and report them.

### 4.4 Launch

- `aiw` or `aiw launch`: start the existing interactive `codex` CLI in the current directory.
- `aiw launch PROJECT_PATH -- <CODEX_ARGS...>`: start Codex in the given directory and forward arguments unchanged.

The launcher MUST preserve the user's configured Codex authentication, model, sandbox, approval policy, and CLI options. It MUST NOT add bypass, danger-full-access, or unattended full-auto flags. Normal Codex approval and sandbox controls remain authoritative.

## 5. Architecture and responsibilities

| Component | Responsibility |
|---|---|
| CLI parser | Commands, arguments, concise errors and exit codes |
| Platform paths | Windows vs POSIX user data, Codex config, skills and executable locations |
| Specs source manager | Clone, validate and fast-forward private `ai-specs` checkout |
| Managed installer | Hash-aware install/update/uninstall; preserve unmanaged content |
| Project initializer | Idempotent AGENTS block and durable project state |
| Doctor/status | Read-only health and provenance reporting |
| Codex launcher | Forward to the existing Codex executable without changing its security flags |
| Bundled AI Workbench skill | Runtime translation of the six mechanisms into conditional agent behavior |

All filesystem writes MUST be atomic where practical. No credentials or tokens are written to files. Git subprocesses use argument arrays (never shell interpolation). A dirty specs checkout is not automatically reset or overwritten.

## 6. Runtime behavior contract

The installed global instruction block and AI Workbench skill MUST cause Codex to:

1. Treat the latest user request as the active goal and supersede obsolete work when the user narrows or changes scope.
2. Distinguish user-confirmed facts, observed implementation facts, verified outcomes, hypotheses and unknowns.
3. Identify the actual repository, worktree, branch, cwd, runtime and entry point before making changes.
4. Locate and reuse existing UI components, APIs, data models and environment capabilities before creating replacements.
5. Select implementation depth from the requested outcome and impact: do not turn exploration into a second product, and do not leave confirmed business behavior as a disconnected mock.
6. Use the relevant current source skills. Apply writing-specs/plans for work that needs them, TDD for behavior-changing production code, task-execution-discipline for plan tasks, and auditing-finding-closure when a confirmed finding is claimed as remediated.
7. Keep one primary agent accountable for end-to-end completion. Delegate only independent work with explicit boundaries and integration proof.
8. Verify the final code state, not an earlier state. State which checks ran, their scope, and what remains unverified.
9. Keep project state concise and durable for multi-step work; do not dump entire conversation history into permanent context.
10. Ask the user only for missing authority, credentials/access, or a material business decision that cannot be resolved from current evidence.

The runtime skill MUST be conditional and outcome-oriented. It MUST NOT require full-repository scans, a full test suite, multiple agents, plans, or extra documentation for every small change.

## 7. Project state contract

`.ai-workbench/PROJECT_STATE.md` is a concise handoff record, not an alternative source of truth. It contains:
- current project purpose and entry points;
- confirmed architecture/data decisions;
- current active objective only when a multi-step task is underway;
- verified run/test commands and the code state they apply to;
- unresolved unknowns/blockers and next concrete action.

It MUST distinguish observed facts from assumptions and MUST be updated only when a meaningful durable fact or recovery point changes. It MUST NOT become a chronological command log.

## 8. Managed file safety

- Global instructions are inserted between stable AI Workbench markers in `~/.codex/AGENTS.md`; all text outside the markers is preserved.
- Skills are copied to the user skill directory from the current specs checkout. Each managed file hash is recorded.
- If an existing target is not owned by AI Workbench, installation stops with a conflict and does not overwrite it.
- On update, a managed target whose current hash differs from the last recorded managed hash is user-modified; leave it untouched and report a conflict.
- Uninstall removes only unchanged managed content.
- Project `AGENTS.md` content outside its markers is preserved. Project state files are created only if absent.

## 9. Security and permissions

- Never store GitHub tokens, Codex credentials, API keys, or OAuth tokens.
- Use the user's existing Git credential manager/SSH agent for private repository access.
- Do not change Codex config, authentication, model selection, approval mode, or sandbox settings.
- Do not launch Codex with security-bypass flags.
- Do not execute repository scripts during install. The only executed commands are Git operations required to retrieve specs and read-only version/availability checks.
- `doctor` is read-only.
- `init` writes only the managed project files described above.
- `uninstall` is hash-guarded and non-destructive.

## 10. Acceptance criteria

1. The CLI runs on Windows and POSIX using Python 3.10+ standard library only.
2. Install from a repository clone works with either a local specs checkout or Git access to the private specs repository.
3. The current specs commit is recorded and current source skills are installed without modifying their semantics.
4. Existing global/project AGENTS content is preserved exactly outside managed markers.
5. Repeated install/init/update are idempotent.
6. Modified managed files are detected and never overwritten or deleted silently.
7. Doctor accurately reports missing prerequisites and does not claim that Codex authentication or model access is valid without evidence.
8. Launch forwards arguments and working directory to the existing Codex command without injecting unsafe flags.
9. Unit tests cover platform paths, marker merge, idempotency, hash conflicts, uninstall safety, subprocess argument forwarding and failure handling.
10. Documentation provides Windows and WSL install, update, init, doctor, launch, uninstall, private-repository authentication, troubleshooting and limitations.
11. A clean environment smoke test can install from a local specs fixture, initialize a temporary project, run doctor against fake executables, launch a fake Codex executable, update, and uninstall without touching the real user's home.
12. No historical finding is marked closed by the existence or tests of this runtime.

## 11. Explicit limitations

- Codex CLI and account access are external prerequisites.
- Private `ai-specs` access is required for fresh install/update unless a local checkout is supplied.
- The framework improves the operating context and repeatability; it cannot guarantee model behavior or automatically close historical findings.
- Browser UI inspection, external APIs, deployment credentials and project-specific services remain dependent on tools and access available in the target project.
- Windows and WSL are separate environments with separate homes and Codex installations; install once in each environment the user intends to use.
