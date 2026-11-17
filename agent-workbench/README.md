# AI Workbench for Codex

A small cross-platform workflow layer for the existing Codex CLI. It installs current skills from the private wly112488/ai-specs repository, adds a managed global instruction block, initializes projects with durable state, checks installation health, and launches Codex interactively without changing its security settings.

This is not a new model, agent runtime, or replacement for Codex. It makes the audited collaboration mechanisms available in the Windows and WSL CLI environments where Codex already runs.

## What it provides

- **One command:** aiw launches the existing interactive Codex CLI in the current directory.
- **Current rules:** installs task execution, plan execution, dependent plans, TDD, finding closure, writing plans/specs, and rule maintenance skills from the current private ai-specs main branch.
- **Project initialization:** safely adds a managed section to AGENTS.md and creates .ai-workbench/PROJECT_STATE.md for durable project facts and recovery.
- **Health checks:** aiw doctor checks Python, Git, Codex, the source revision, installed skills, managed file integrity, PATH and project initialization.
- **Safe lifecycle:** updates are fast-forward-only; user-edited managed files are never silently overwritten or deleted; uninstall removes only unchanged managed files.
- **No runtime dependencies:** Python 3.10+ standard library only.

## Prerequisites

1. Python 3.10 or newer.
2. Git available on PATH.
3. Codex CLI installed and authenticated in each environment where you will use it.
4. Read access to the private wly112488/ai-specs repository through your existing Git credential manager or SSH agent, unless you provide a local clone.

AI Workbench does not install Codex CLI, create credentials, or validate account authentication. aiw doctor can detect the executable but deliberately does not claim that login/model access is valid.

## Install on Windows

Use PowerShell. Clone this public audit/runtime repository, then run the bootstrap script:

~~~powershell
git clone https://github.com/wly112488/question.git
cd question
py -3 .\agent-workbench\aiw.py install
~~~

The installer retrieves ai-specs using your existing Git authentication. If you use GitHub CLI, configure Git authentication first with gh auth setup-git; otherwise use Git Credential Manager or SSH.

If the installer reports that its launcher directory is not on PATH, add the exact directory printed by the installer to your **user** PATH using the PowerShell command it prints, then open a new terminal. Verify:

~~~powershell
aiw doctor
~~~

## Install on WSL

Run these commands inside the WSL distribution in which Codex CLI is installed:

~~~bash
git clone https://github.com/wly112488/question.git
cd question
python3 agent-workbench/aiw.py install
~~~

Authenticate Git to the private ai-specs repository in WSL independently of Windows (for example, configure SSH or gh auth login). If needed, add the printed PATH entry to ~/.bashrc or the profile for your shell:

~~~bash
export PATH="$HOME/.local/bin:$PATH"
~~~

Open a new terminal, then run:

~~~bash
aiw doctor
~~~

**Windows and WSL are separate installations.** They have separate home directories, Codex binaries, credentials, global instructions and skills. Install once in each environment you intend to use.

## If you already have a local ai-specs clone

If private Git authentication is not configured in the current environment, pass an existing clean clone on main:

~~~powershell
py -3 .\agent-workbench\aiw.py install --specs-dir C:\path\to\ai-specs
~~~

~~~bash
python3 agent-workbench/aiw.py install --specs-dir ~/src/ai-specs
~~~

The explicit local path is used as-is after checking its remote, branch, cleanliness and required source files. aiw update performs a fast-forward update and therefore requires the clone's remote to be reachable.

## Use in a project

Initialize each project once:

~~~powershell
aiw init C:\work\my-project
~~~

~~~bash
aiw init ~/work/my-project
~~~

This operation:

- appends a managed block to the project's root AGENTS.md, preserving all content outside the markers;
- creates .ai-workbench/PROJECT_STATE.md as a concise durable handoff record;
- creates .ai-workbench/config.json and .ai-workbench/managed.json only when absent.

Existing AGENTS.md, project state and config are not replaced. If a managed block is later edited or ownership is ambiguous, initialization stops and asks for manual resolution rather than overwriting it.

Then open the project directory in your terminal and run:

~~~bash
aiw
~~~

This starts the existing interactive Codex CLI in the current directory. To launch in a different directory or forward Codex options:

~~~bash
aiw launch ~/work/my-project -- --model <model-name>
~~~

AI Workbench does not inject --full-auto, --dangerously-bypass-approvals-and-sandbox, or other permission-bypass flags. Codex retains the user's configured sandbox, approval policy, model and authentication.

## Commands

| Command | Purpose |
|---|---|
| aiw | Launch interactive Codex in the current directory |
| aiw launch [path] -- [codex args...] | Launch Codex in a project and forward arguments |
| aiw install [--specs-dir path] | Install managed instructions, skills and launcher |
| aiw update [--specs-dir path] | Fast-forward ai-specs/main and safely refresh managed files |
| aiw init [project-path] | Initialize project instructions and durable state |
| aiw doctor | Run read-only environment and installation checks |
| aiw status | Show installed source revision and managed file count |
| aiw uninstall | Remove unchanged AI Workbench-managed files only |

aiw uninstall intentionally leaves project AGENTS.md blocks and .ai-workbench/ state in place: it does not crawl the filesystem to find projects. Remove a project's AI Workbench block manually only if you no longer want that project to use the workflow. The ai-specs checkout is also retained so it can be reused or inspected.

## How the workflow is applied

The runtime skill translates the solution design into six mechanisms: current intent/state, evidence-driven engineering location, progressive implementation and data adaptation, recoverable execution, final-state-bound verification, and bounded information/agent orchestration. It also invokes the relevant current ai-specs skills only when their triggers apply.

It is intentionally not a rigid checklist. Small UI changes should remain small; multi-step work should preserve a concise recovery state; confirmed findings require their original-finding proof before they can be reported closed. The historical 607 records remain evidence, not a claim that installing this CLI retroactively closes every finding.

## Model-behavior evaluation

See [VALIDATION_REPORT.md](VALIDATION_REPORT.md) for the exact automated checks and environment limitations.


EVALUATION.md contains ten disposable-project scenarios for checking actual Codex behavior (scope changes, component/API reuse, prototype-to-production transition, environment identity, recovery, final-state verification, finding closure and proportionate workflow). Automated tests cannot prove model compliance; use these scenarios to evaluate the model and tools available in your own Windows/WSL setup.

## Update and conflict handling

- aiw update checks that the ai-specs checkout is on main and clean, then runs git pull --ff-only.
- The installed manifest records the upstream commit and SHA-256 hashes of managed files.
- A modified managed skill, launcher or global instruction block is reported as a conflict and is not overwritten.
- A failed installation attempts to restore files to their pre-install state.
- To use an explicit local clone without pulling during install, run aiw install --specs-dir <path>. A later aiw update --specs-dir <path> performs the fast-forward update.

## Development and tests

From this directory:

~~~bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q ai_workbench aiw.py
python3 aiw.py --help
~~~

The tests use temporary homes, local fake specs checkouts and fake Codex executables. They do not touch the developer's actual Codex configuration, require model calls, or prove that a remote Codex account is authenticated. CI runs the same suite on Windows and Ubuntu.

## Limitations

- This is a workflow and installation layer, not a guarantee that a model will always follow instructions or solve every task correctly.
- It does not supply missing project-specific APIs, browser automation, deployment credentials, external service access or business decisions.
- A successful install or aiw doctor does not prove that Codex can authenticate, that a model is available, or that a target project is deployable.
- Historical findings are not automatically closed. Remediation claims still require the original finding's acceptance proof.
