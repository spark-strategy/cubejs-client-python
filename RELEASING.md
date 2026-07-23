# Releasing

The package is published to PyPI as
[`cubejs-client-python`](https://pypi.org/project/cubejs-client-python/) via
**Trusted Publishing** (OIDC) — no API token is stored in this repo.

> **The PyPI project name must exactly match `name` in `pyproject.toml`**
> (`cubejs-client-python`). It is *not* inferred from the repo. A mismatch produces the
> confusing `400 Non-user identities cannot create new projects` error described below.
> Note the import name is still `cubejs_client`; only the distribution name has the suffix.

## One-time setup

Because the project does not exist on PyPI until its first successful upload, and a Trusted
Publisher is a **non-user identity** that cannot create a new project on its own, the first
release has to be bootstrapped one of two ways.

### Option A — pending publisher (recommended, no tokens)

1. Go to **https://pypi.org/manage/account/publishing/** (account level — the per-project
   *Publishing* tab only exists once the project does).
2. Under **Add a new pending publisher**, enter:

   | Field | Value |
   | --- | --- |
   | PyPI Project Name | `cubejs-client-python` ← must match `pyproject.toml` |
   | Owner | `spark-strategy` |
   | Repository name | `cubejs-client-python` |
   | Workflow name | `release.yml` |
   | Environment | `pypi` |

3. Run the release. The first successful publish promotes the pending publisher to a real one.

### Option B — bootstrap with a user token

Account Settings → API tokens → **Add API token, scope "Entire account"** (a *user* identity,
so it may create projects). Upload once with `twine upload dist/*`, then configure the trusted
publisher normally and delete the token.

### Then, for both options

4. Repeat on [TestPyPI](https://test.pypi.org) with environment `testpypi` if you want
   dry-run uploads.
5. In GitHub: **Settings → Environments**, create `pypi` (and `testpypi`). Adding a required
   reviewer to `pypi` gives you a manual approval gate before anything goes public.

## Troubleshooting

**`400 Non-user identities cannot create new projects`** — the project doesn't exist yet and
you're authenticating as a Trusted Publisher. Either the pending publisher is missing, or its
**PyPI Project Name doesn't match `name` in `pyproject.toml`**. See Option A above.

**Wheel filename uses an underscore** (`cubejs_client_python-0.1.0-...whl`) — expected. PEP 625
normalizes `-` to `_` in artifact filenames; it does not affect the install name.

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
            --extra-index-url https://pypi.org/simple cubejs-client-python
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
