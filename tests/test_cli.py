from types import SimpleNamespace

from wslc_compose import cli
from wslc_compose.model import Project


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


def test_project_containers_accepts_wslc_list_field_names(monkeypatch):
    monkeypatch.setattr(
        cli.engine,
        "list_project_containers",
        lambda project, all_states=False: [
            {
                "ID": "a53e9fdf3408",
                "Names": "oracle",
                "Image": "example/oracle:slim",
                "Ports": "127.0.0.1:1521->1521/tcp",
            }
        ],
    )
    inspected = []

    def fake_inspect(identifier):
        inspected.append(identifier)
        return {
            "Labels": {
                "com.wslc-compose.service": "oracle",
                "com.wslc-compose.container-number": "1",
                "com.wslc-compose.config-hash": "abc123",
            },
            "State": {"Running": True, "Status": "running"},
        }

    monkeypatch.setattr(cli.engine, "inspect", fake_inspect)

    containers = cli._project_containers(Project(name="user-service", directory="."))

    assert inspected == ["a53e9fdf3408"]
    assert containers == [
        {
            "id": "a53e9fdf3408",
            "name": "oracle",
            "image": "example/oracle:slim",
            "service": "oracle",
            "index": 1,
            "hash": "abc123",
            "running": True,
            "status": "running",
            "ports": "127.0.0.1:1521->1521/tcp",
        }
    ]
    assert cli._format_ports(containers[0]["ports"]) == "127.0.0.1:1521->1521/tcp"
