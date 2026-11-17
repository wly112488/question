# Validation report

## Automated checks

- Python unit/smoke suite: 29 tests are defined across core path/marker handling, source-skill validation, safe project initialization, install/update/uninstall, rollback, manifest path confinement and CLI launching.
- A real local Git checkout is used to verify branch, cleanliness, remote identity and current commit handling.
- A POSIX end-to-end integration test creates a temporary Git-backed ai-specs fixture, installs into an isolated HOME/XDG data directory, initializes a disposable project, launches the installed shim against a fake Codex executable, runs aiw doctor, and uninstalls only unchanged global/runtime files.
- Windows and Ubuntu GitHub Actions matrix is configured for Python 3.10 and 3.13.
- Python bytecode compilation, CLI help/version and Python 3.10 grammar compatibility are checked locally.

## Environment boundary

The build environment used for this implementation does not have the user's Codex CLI or private ai-specs credentials. The integration test uses a local fixture with the expected repository identity and a fake Codex executable; it validates the installation/launcher mechanics, not live model authentication or model behavior.

The Windows CI job validates Windows paths, managed-file operations and the Windows launcher generation, but does not run a real Windows Codex installation. The actual Windows/WSL deployment must be verified in the user's authenticated environment with aiw doctor.

## Required first-run actions

1. Install and authenticate Codex CLI in each environment (Windows and/or WSL).
2. Ensure Git can read the private wly112488/ai-specs repository, or provide a clean local clone with aiw install --specs-dir.
3. Add the printed launcher directory to PATH and reopen the terminal.
4. Run aiw doctor and aiw init in the project directory.

No Codex permissions or sandbox settings are changed by the launcher.
