"""Shared fixtures: make external probes deterministic and offline.

Several verbs shell out to docker / nvidia-smi and probe ``/health``. The
autouse fixture below neutralises those so the suite never depends on a running
container, a GPU, or the host's ``~/.model-gear`` — every probe degrades to its
"nothing there" answer. Tests that need a deployment scaffold one into a tmp dir
and pass ``--compose-dir``.
"""

from __future__ import annotations

import pytest

from model_gear.runtime import _compose, _health


@pytest.fixture(autouse=True)
def offline_runtime(monkeypatch, tmp_path):
    # docker / nvidia-smi best-effort probes → "not available".
    monkeypatch.setattr(_compose, "_probe", lambda *a, **k: None)
    # /health never responds.
    monkeypatch.setattr(_health, "is_healthy", lambda *a, **k: False)
    # No deployment scaffolded by default: point the home at an empty tmp dir.
    monkeypatch.delenv("MODEL_GEAR_DIR", raising=False)
    empty = tmp_path / "home-model-gear"
    monkeypatch.setattr(_compose, "default_deployment_dir", lambda: empty)
