from types import SimpleNamespace

from wslc_compose import cli


def test_ps_accepts_all_option():
    parser = cli.build_parser()

    assert parser.parse_args(["ps"]).all is False
    assert parser.parse_args(["ps", "-a"]).all is True
    assert parser.parse_args(["ps", "--all"]).all is True


def test_ps_uses_all_flag_when_requested(monkeypatch):
    calls = []
    project = SimpleNamespace(name="demo")
    ns = SimpleNamespace(all=True, services=[], quiet=False)

    monkeypatch.setattr(cli, "_load", lambda _: project)
    monkeypatch.setattr(
        cli,
        "_project_containers",
        lambda _, all_states=False: calls.append(all_states) or [],
    )

    assert cli.cmd_ps(ns) == 0
    assert calls == [True]


def test_ps_excludes_stopped_by_default(monkeypatch):
    calls = []
    project = SimpleNamespace(name="demo")
    ns = SimpleNamespace(all=False, services=[], quiet=False)

    monkeypatch.setattr(cli, "_load", lambda _: project)
    monkeypatch.setattr(
        cli,
        "_project_containers",
        lambda _, all_states=False: calls.append(all_states) or [],
    )

    assert cli.cmd_ps(ns) == 0
    assert calls == [False]


def test_down_still_includes_stopped_containers(monkeypatch):
    calls = []
    project = SimpleNamespace(name="demo", networks={}, volumes={})
    ns = SimpleNamespace(timeout=10, dry_run=False, volumes=False)

    monkeypatch.setattr(cli, "_load", lambda _: project)
    monkeypatch.setattr(
        cli,
        "_project_containers",
        lambda _, all_states=False: calls.append(all_states) or [],
    )
    monkeypatch.setattr(cli.engine, "network_names", lambda: [])

    assert cli.cmd_down(ns) == 0
    assert calls == [True]
