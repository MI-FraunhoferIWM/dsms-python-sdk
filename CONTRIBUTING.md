# Contributing to DSMS Python SDK

Thank you for considering a contribution! This document explains how to set up a development environment, run the checks we require, and submit changes.

---

## Table of Contents

1. [Development setup](#development-setup)
2. [Code style and linting](#code-style-and-linting)
3. [Pre-commit hooks](#pre-commit-hooks)
4. [Testing](#testing)
5. [Branching and commits](#branching-and-commits)
6. [Opening a pull request](#opening-a-pull-request)
7. [Versioning](#versioning)
8. [Reporting issues](#reporting-issues)

---

## Development setup

```bash
git clone git@github.com:MI-FraunhoferIWM/dsms-python-sdk.git
cd dsms-python-sdk
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

The `[dev]` extra installs all development dependencies including linters, test runners, and the pre-commit framework.

---

## Code style and linting

We enforce a consistent style automatically via pre-commit hooks (see below). The key rules are:

| Tool      | Configuration                                 |
|:---------:|:---------------------------------------------:|
| `black`   | Line length 79, enforced on all `.py` files   |
| `isort`   | Profile `black`, line length 79               |
| `flake8`  | Default rules, line length inferred from black |
| `pylint`  | `fail-under=10.0`; see `.pylintrc` for disabled checks |
| `bandit`  | Security linting                              |
| `pyupgrade` | Enforces modern Python syntax              |

Do **not** bypass hooks with `--no-verify`. If a hook fails, fix the underlying issue.

---

## Pre-commit hooks

Install the hooks once after cloning:

```bash
pip install pre-commit
pre-commit install
```

Run manually against all changed files:

```bash
pre-commit run --files <file1> <file2> ...
```

Run against all files in the repo:

```bash
pre-commit run --all-files
```

To update hook versions to the latest stable releases:

```bash
pre-commit autoupdate
```

---

## Testing

Run the unit test suite with:

```bash
pytest
```

Tests live under `tests/`. We do not mock the database in integration tests — if you add a test that touches the backend, it must run against a real DSMS instance configured via environment variables (see `Configuration` in `dsms/core/configuration.py`).

**Tutorial notebooks** can be tested against a live instance with:

```bash
./scripts/run_notebooks.sh
```

To re-execute notebooks and save outputs in-place (for documentation commits):

```bash
./scripts/run_notebooks.sh --refresh
```

See `scripts/run_notebooks.sh --help` (or read the script header) for full usage. Requires `pip install -e ".[docs,tests]"` and a reachable DSMS instance.

---

## Branching and commits

- Base feature branches off `main`.
- Use descriptive branch names, e.g. `feature/ktype-v2-subsystem` or `fix/search-context-filter`.
- Keep commits focused. One logical change per commit.
- Write commit messages in the imperative mood: *"Add schema_data field to KItem"*, not *"Added"* or *"Adding"*.
- Do not amend published commits.

---

## Opening a pull request

1. Push your branch and open a PR against `main`.
2. Fill in the PR template — at minimum, describe **what** changed and **why**.
3. Ensure all CI checks pass before requesting a review.
4. Add an entry to `CHANGELOG.md` under the relevant unreleased section.
5. Update any affected documentation in `docs/`.

PRs that introduce new public API surface should update:
- `dsms/knowledge/__init__.py` — re-export new models.
- `docs/dsms_sdk/dsms_kitem_schema.md` or `docs/dsms_sdk/dsms_sdk.md` — document new fields/methods.

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html):

- **MAJOR** — breaking API changes.
- **MINOR** — backward-compatible new functionality.
- **PATCH** — backward-compatible bug fixes.

The version is set in `setup.cfg` (`version = vMAJOR.MINOR.PATCH`). Update it and `CHANGELOG.md` together as part of a release PR.

The SDK version must stay compatible with the target DSMS backend version. See the compatibility table in `README.md`.

---

## Reporting issues

Please open an issue at <https://github.com/MI-FraunhoferIWM/dsms-python-sdk/issues> and include:

- SDK version (`pip show dsms-sdk`).
- Python version.
- A minimal reproducible example.
- The full traceback if applicable.
