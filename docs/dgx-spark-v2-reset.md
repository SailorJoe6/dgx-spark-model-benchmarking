# DGX Spark v2 Reset and Tool-Calling Migration

This document captures the post-migration state for the DGX Spark v2 reset and
mini-swe-agent v2 tool-calling transition.

## Target State Summary

- All configs in `configs/*-livesweagent.yaml` are v2 tool-calling compatible.
- `model.model_class` is `litellm` and v1 parsing keys are removed.
- Configs are regenerated from `configs/livesweagent.template.yaml`.
- Tests pass locally with the repo venv.
- Repo-managed git hooks enforce tests before commit.

## System Requirements (mini-swe-agent v2)

The mini-swe-agent v2 test suite relies on bubblewrap and requires:

- `uidmap` installed (provides `newuidmap`/`newgidmap`).
- Unprivileged user namespaces enabled (AppArmor setting on Ubuntu 24.04).
- `/lib64` present (symlink to `/lib` on Ubuntu 24.04).

## Tests

Run all tests with the repo venv:

```bash
source work/swebench/.venv/bin/activate

# Repo tests
python -m unittest discover -s tests -v

# mini-swe-agent tests
cd work/swebench/mini-swe-agent
python -m pytest -q
```

## Hooks

This repo uses repo-managed git hooks. Install once per clone:

```bash
scripts/git-hooks/install.sh
```

The `pre-commit` hook runs:

- `python -m unittest discover -s tests -v`
- `python -m pytest -q` in `work/swebench/mini-swe-agent`

## Config Migration Notes

- `action_observation_template` moved to `model.observation_template`.
- `format_error_template` moved to `model.format_error_template`.
- `timeout_template` removed from `agent`.
- `action_regex` removed (tool calling does not use it).
- Regenerate configs with:
  - `scripts/agentic/generate_livesweagent_configs.py`

