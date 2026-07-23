# Releasing

The package is published to PyPI as [`cubejs-client`](https://pypi.org/project/cubejs-client/)
via **Trusted Publishing** (OIDC) — no API token is stored in this repo.

## One-time setup

1. Create the project on PyPI (or claim the name with a first manual upload).
2. On PyPI: **Manage project → Publishing → Add a new publisher (GitHub)**

   | Field | Value |
   | --- | --- |
   | Owner | `spark-strategy` |
   | Repository | `cubejs-client-python` |
   | Workflow name | `release.yml` |
   | Environment | `pypi` |

3. Repeat on [TestPyPI](https://test.pypi.org) with environment `testpypi` if you want
   dry-run uploads.
4. In GitHub: **Settings → Environments**, create `pypi` (and `testpypi`). Adding a required
   reviewer to `pypi` gives you a manual approval gate before anything goes public.

## Cutting a release

1. Bump `version` in `pyproject.toml` (PyPI versions are **immutable** — a version can never
   be re-uploaded, even after deletion).
2. Commit and merge to `main`.
3. Tag and push:

   ```bash
   git tag v0.1.0
   git push --tags
   ```

The `Release` workflow verifies the tag matches `pyproject.toml`, builds the sdist + wheel,
runs `twine check`, and publishes to PyPI.

## Dry run first

Use **Actions → Release → Run workflow** with target `testpypi`, then verify the install:

```bash
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple cubejs-client
```

(The extra index is needed because TestPyPI does not mirror `pandas`/`httpx`.)

## Building locally

```bash
python -m pip install --upgrade build twine
rm -rf dist && python -m build
twine check dist/*
```

## Release checklist

- [ ] CI green on `main`, including the **3.9** matrix leg (that leg is what actually
      substantiates `requires-python = ">=3.9"`)
- [ ] `version` bumped in `pyproject.toml`
- [ ] `README.md` / `API_REFERENCE.md` reflect any API changes
- [ ] Tag matches the version exactly (`v0.1.0` ↔ `0.1.0`)
