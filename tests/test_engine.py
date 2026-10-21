import subprocess

import pytest

from wslc_compose import engine
from wslc_compose.engine import WslcError


def _ok(args):
    return subprocess.CompletedProcess(args, 0, "", "")


def test_run_retried_recovers_from_transient_error(monkeypatch):
    calls = []

    def fake_run(args, capture=False, check=True, dry_run=False):
        calls.append(list(args))
        if len(calls) == 1:
            raise WslcError(
                "wslc start foo failed (exit 1): Impossible de créer un fichier "
                "déjà existant. Code d'erreur : ERROR_ALREADY_EXISTS"
            )
        return _ok(args)

    monkeypatch.setattr(engine, "run", fake_run)
    monkeypatch.setattr(engine.time, "sleep", lambda s: None)

    proc = engine.run_retried(["start", "foo"])
    assert proc.returncode == 0
    assert len(calls) == 2


def test_run_retried_gives_up_after_max_attempts(monkeypatch):
    calls = []

    def fake_run(args, capture=False, check=True, dry_run=False):
        calls.append(list(args))
        raise WslcError("wslc start foo failed (exit 1): ERROR_SHARING_VIOLATION")

    monkeypatch.setattr(engine, "run", fake_run)
    monkeypatch.setattr(engine.time, "sleep", lambda s: None)

    with pytest.raises(WslcError):
        engine.run_retried(["start", "foo"], retries=3)
    assert len(calls) == 3


def test_run_retried_does_not_retry_other_errors(monkeypatch):
    calls = []

    def fake_run(args, capture=False, check=True, dry_run=False):
        calls.append(list(args))
        raise WslcError("wslc start foo failed (exit 1): no such container")

    monkeypatch.setattr(engine, "run", fake_run)
    monkeypatch.setattr(engine.time, "sleep", lambda s: None)

    with pytest.raises(WslcError):
        engine.run_retried(["start", "foo"])
    assert len(calls) == 1


def test_list_project_containers_excludes_stopped_by_default(monkeypatch):
    calls = []

    def fake_capture_json(args):
        calls.append(args)
        return []

    monkeypatch.setattr(engine, "capture_json", fake_capture_json)

    assert engine.list_project_containers("demo") == []
    assert calls == [
        ["list", "--format", "json", "-f", "label=com.wslc-compose.project=demo"]
    ]


def test_list_project_containers_includes_all_states_when_requested(monkeypatch):
    calls = []

    def fake_capture_json(args):
        calls.append(args)
        return []

    monkeypatch.setattr(engine, "capture_json", fake_capture_json)

    assert engine.list_project_containers("demo", all_states=True) == []
    assert calls == [
        ["list", "-a", "--format", "json", "-f", "label=com.wslc-compose.project=demo"]
    ]
