# Project Context

# Project Context

## Purpose
This repository (pgdev) is a local PostgreSQL development and debugging workspace. It is intended for:
- Building and testing PostgreSQL from source (one or more upstream trees under `upstream/`).
- Fast iteration on core patches and experimental features.
- Debugging and introspection of server internals via helper scripts and GDB pretty-printers (examples: `pg_print_tree_gdb.py`, `pg_printer.py`, `table_slot_printer.py`).

## Tech Stack
- PostgreSQL (C) — core server source under `upstream/` (e.g. `upstream/19-dev/`).
- Python 3 — utility scripts and debug helpers in repository root.
- Shell / Make — build and test orchestration.
- GDB — debugging server processes and using Python-based pretty-printers.
- Standard GNU toolchain: `gcc/clang`, `make`, `autoconf`/`automake` (as required by the upstream source).

## Project Layout (important paths)
- `upstream/` — upstream PostgreSQL source trees and per-version debug builds (e.g. `upstream/19-dev/`).
- `build/` — local build artifacts (intermediate objects).
- `install/` — staged `make install` output for local runtimes.
- `data/` — Postgres data directories used for running test instances.
- `bin/` — helper binaries or wrappers used by the project.
- `openspec/` — project specifications and change proposals; follow the OpenSpec workflow.
- scripts at repo root: `pg_print_tree_gdb.py`, `pg_printer.py`, `table_slot_printer.py` — developer tools for inspecting server state.

## Conventions

### Coding & Style
- C code: Follow upstream PostgreSQL coding conventions when modifying `upstream/` sources.
- Python: follow PEP 8; prefer a virtual environment per developer. Use `python3 -m venv .venv` and `pip install -r requirements.txt` if a `requirements.txt` is added.
- Shell: POSIX-compatible `sh`/`bash` scripting; avoid non-portable constructs where possible.

### Branching & Git
- Prefer short-lived feature branches: `feature/<short-desc>` or `fix/<short-desc>`.
- Use descriptive commit messages; include `openspec` change-ids when a spec/proposal is involved.
- For larger changes affecting project capabilities, create an `openspec/changes/<change-id>/` via the OpenSpec process.

### Openspec / Change Proposals
- Follow `openspec/AGENTS.md` for proposal structure and validation. Choose verb-led change-ids (e.g. `add-gdb-printers`, `refactor-build-scripts`).

## Build & Run (examples)
These are example workflows; adapt flags to your environment and upstream source.

1) Prepare Python environment (optional but recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
# pip install -r requirements.txt   # if requirements file exists
```

2) Build upstream PostgreSQL (example for `upstream/19-dev`):

```bash
cd upstream/19-dev
# Configure with debug/asserts as needed (example flags):
./configure --prefix=$PWD/../../install/19-dev/debug --enable-debug --enable-cassert
make -j$(nproc)
make install
```

3) Initialize a data directory and start a local instance (example):

```bash
install/19-dev/debug/bin/initdb -D ../../../data/19-dev
install/19-dev/debug/bin/pg_ctl -D ../../../data/19-dev -l ../../../logs/19-dev.log start
```

4) Use gdb and debug helpers:

```bash
# Run the server under gdb or attach to a running process
gdb --args install/19-dev/debug/bin/postgres -D data/19-dev
# In gdb, load Python pretty-printers if required, or use the provided scripts directly
python3 pg_print_tree_gdb.py --help
```

## Testing
- Use `make check` inside the upstream source where supported (e.g. `upstream/19-dev`).
- Add focused regression tests for core behavior when introducing patches. Keep tests small and deterministic.

## Contributor Guidelines
- Before implementing feature-level changes, create an OpenSpec proposal under `openspec/changes/<change-id>/`.
- Run validations: `openspec validate <change-id> --strict --no-interactive` when appropriate.
- Keep the repo reproducible: document any non-obvious host dependencies (specific compiler versions, system packages) in this file or README.

## Environment & Tooling
- Host OS: Linux is the primary development target for build and debug flows.
- Recommended: Python >= 3.10, recent `gcc`/`clang`, `gdb` with Python support.

## Notes & Constraints
- The repo contains upstream snapshots — be careful when rebasing or applying patches onto upstream trees.
- Debug builds may require additional disk space and longer compile times; use `--enable-debug` and `--enable-cassert` only where needed.

## Where to find help
- For OpenSpec and change workflow, read `openspec/AGENTS.md` and follow the Quick Start examples.
- For local debugging helpers, inspect the scripts in repo root (they include usage examples and `--help`).

---

If you'd like, I can:
- Add a small `requirements.txt` for the Python helpers, or
- Add a short `Makefile` target in the repo root with common commands (build/start/debug).
