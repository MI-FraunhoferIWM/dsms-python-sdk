# Release Checklist

Work through this list in order when preparing a new SDK release. Each section states which files to touch and what to verify.

Commands assume your working directory is the **repository root** and your virtual environment is active:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[docs,tests,pre_commit]"
```

---

## 0. Classify the change

Determine the semantic-versioning impact before touching any file:

| Change type | Version bump | Examples |
|---|---|---|
| Typo, doc fix, internal refactor with no API change | **patch** (x.y.Z) | Fix docstring, rename internal variable |
| New field, method, or parameter (backward-compatible) | **minor** (x.Y.0) | Add `schema_data` field to `KItem` |
| Removed or renamed public API, breaking model change | **major** (X.0.0) | Rename `user_groups` to `access_properties`, drop Python version |

---

## 1. `setup.cfg`

- [ ] Bump `version` to the new version string (format: `vMAJOR.MINOR.PATCH`).
- [ ] Update `python_requires` if the minimum Python version changed.
- [ ] Add, remove, or relax dependency pins in `install_requires` if needed.

**Verify:**

```bash
python -c "import configparser; c = configparser.ConfigParser(); c.read('setup.cfg'); print(c['metadata']['version'])"
```

---

## 2. `CHANGELOG.md`

- [ ] Add a new version section **above** the previous entry:

  ```markdown
  ## [x.y.z] — YYYY-MM-DD

  ### Added
  - ...

  ### Changed
  - ...

  ### Deprecated
  - ...

  ### Removed
  - ...

  ### Fixed
  - ...
  ```

- [ ] Use today's date in `YYYY-MM-DD` format.
- [ ] Cover every public API change, new model, and deprecation.

---

## 3. `README.md`

- [ ] Update the compatibility table: add a row for the new SDK version and its required DSMS backend version.
- [ ] Update the Usage capabilities list if new top-level features were added.

---

## 4. `docs/dsms_sdk/dsms_sdk.md`

- [ ] Update the compatibility table to match `README.md`.
- [ ] Update the numbered capabilities list if the feature set changed.

---

## 5. `docs/dsms_sdk/dsms_kitem_schema.md`

Update this file when any of the following change:

- [ ] New or removed fields on `KItem` or `KItemCompactedModel`: update the field tables.
- [ ] New property sub-models (e.g. `KItemAccessProperties`, `KItemSchemaData`): add a dedicated section with field table and example.
- [ ] New or removed `Widget` enum values: update the Widget Fields table.
- [ ] Deprecated fields: mark them clearly in the table and add a deprecation note.

---

## 6. `docs/dsms_sdk/dsms_config_schema.md`

- [ ] Update the Configuration Fields table if any `Configuration` fields were added, removed, or changed.

---

## 7. Tutorial notebooks

Update notebooks when any of the following change:

- [ ] Public API signatures (`DSMS.search()`, `DSMS.get_kitems()`, `KItem` fields, etc.)
- [ ] New features worth demonstrating (new search filters, new KType v2 methods, new property models)
- [ ] Deprecated fields used in notebook code cells

Work cell by cell. Do **not** hand-edit output cells; regenerate them with the refresh script (see step 8).

Notebooks live in `docs/dsms_sdk/tutorials/`. Specific guidance:

| Notebook | When to update |
|---|---|
| `1_introduction.ipynb` | KItem/KType field changes, new top-level SDK features |
| `2_creation.ipynb` | New KItem fields, new `access_properties` / `schema_data` patterns |
| `3_updating.ipynb` | Changed update workflows, new updatable fields |
| `4_deletion.ipynb` | Changed deletion behaviour |
| `5_search.ipynb` | New `DSMS.search()` parameters or filters |
| `6_apps.ipynb` | App config or pipeline changes |
| `7_ktypes.ipynb` | KType v1 or v2 API changes |
| `8_kitem_contexts.ipynb` | Context model or context-scoped SPARQL changes |

---

## 8. Run and refresh notebooks

> **Requirement:** a live DSMS instance must be reachable. Set credentials in a `.env` file or via environment variables (`DSMS_HOST_URL`, `DSMS_USERNAME`, `DSMS_PASSWORD` or `DSMS_TOKEN`) before running.

**Test all notebooks without saving outputs (CI-safe):**

```bash
./scripts/run_notebooks.sh
```

**Re-execute and save outputs in-place (for documentation commits):**

```bash
./scripts/run_notebooks.sh --refresh
```

**Refresh a single notebook:**

```bash
./scripts/run_notebooks.sh --refresh docs/dsms_sdk/tutorials/7_ktypes.ipynb
```

Inspect the saved outputs before committing:

- Every code cell must have output (no silent failures).
- No cell output should contain a Python traceback.
- Deprecated-field warnings (if any) should appear in the expected cells only.

---

## 9. Pre-commit hooks

Run all linters and formatters across every changed Python file:

```bash
pre-commit run --files <file1> <file2> ...
```

All hooks must pass before committing. Do not use `--no-verify`.

---

## 10. Commit and tag

- [ ] Stage files by name; do not use `git add .` or `git add -A`.
- [ ] Write a concise commit message: `release: bump to vX.Y.Z`
- [ ] Tag the release commit:

  ```bash
  git tag vX.Y.Z <commit-sha>
  git push origin vX.Y.Z
  ```

- [ ] Verify the tag is visible on the remote:

  ```bash
  git ls-remote --tags origin | grep vX.Y.Z
  ```

---

## 11. PyPI publish

- [ ] Build the distribution:

  ```bash
  python -m build
  ```

- [ ] Upload to PyPI:

  ```bash
  twine upload dist/dsms_sdk-X.Y.Z*
  ```

- [ ] Verify the new version is visible at https://pypi.org/project/dsms-sdk/.

---

## Quick reference

| File | patch | minor | major |
|---|:---:|:---:|:---:|
| `setup.cfg` (version) | yes | yes | yes |
| `CHANGELOG.md` | yes | yes | yes |
| `README.md` (compat table) | no | yes | yes |
| `README.md` (capabilities) | no | maybe | yes |
| `docs/dsms_sdk/dsms_sdk.md` | no | maybe | yes |
| `docs/dsms_sdk/dsms_kitem_schema.md` | no | yes | yes |
| `docs/dsms_sdk/dsms_config_schema.md` | no | maybe | yes |
| Tutorial notebooks | no | maybe | yes |
| Run `scripts/run_notebooks.sh` | no | yes | yes |
