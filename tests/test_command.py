from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import override_settings

from ptech_tools.management.commands import export_db as export_db_command


def test_export_db_command_uses_service(monkeypatch):
    captured = {}

    class DummyService:
        def __init__(self, config, *, connection=None, runner=None, clock=None):
            captured["config"] = config

        def export(self):
            return Path("/tmp/export.sql")

    monkeypatch.setattr(export_db_command, "ExportDBService", DummyService)

    stdout = StringIO()
    call_command(
        "export_db",
        database="reports",
        output_dir="/tmp/backups",
        stdout=stdout,
    )

    assert "Exported database to /tmp/export.sql" in stdout.getvalue()
    assert captured["config"].database_alias == "reports"
    assert captured["config"].output_dir == Path("/tmp/backups")
    assert captured["config"].compress is False
    assert captured["config"].include_tables == ()
    assert captured["config"].exclude_tables == ()


def test_export_db_command_supports_dry_run(monkeypatch):
    class DummyService:
        def __init__(self, config, *, connection=None, runner=None, clock=None):
            self.config = config

        def build_target_path(self):
            return Path("/tmp/dry-run.sql")

    monkeypatch.setattr(export_db_command, "ExportDBService", DummyService)

    stdout = StringIO()
    call_command("export_db", dry_run=True, stdout=stdout)

    assert stdout.getvalue().strip() == "/tmp/dry-run.sql"


def test_export_db_command_passes_expansion_options(monkeypatch):
    captured = {}

    class DummyService:
        def __init__(self, config, *, connection=None, runner=None, clock=None):
            captured["config"] = config

        def export(self):
            return Path("/tmp/export.sql.gz")

    monkeypatch.setattr(export_db_command, "ExportDBService", DummyService)

    stdout = StringIO()
    call_command(
        "export_db",
        database="reports",
        output_dir="/tmp/backups",
        include_tables=["users", "orders"],
        exclude_tables=["audit_log"],
        compress=True,
        stdout=stdout,
    )

    assert captured["config"].compress is True
    assert captured["config"].include_tables == ("users", "orders")
    assert captured["config"].exclude_tables == ("audit_log",)
    assert "Exported database to /tmp/export.sql.gz" in stdout.getvalue()


@override_settings(PTECH_TOOLS={"EXPORT_DB": {"compress": True}})
def test_export_db_command_keeps_settings_compress_when_flag_is_omitted(monkeypatch):
    captured = {}

    class DummyService:
        def __init__(self, config, *, connection=None, runner=None, clock=None):
            captured["config"] = config

        def export(self):
            return Path("/tmp/export.sql.gz")

    monkeypatch.setattr(export_db_command, "ExportDBService", DummyService)

    stdout = StringIO()
    call_command("export_db", stdout=stdout)

    assert captured["config"].compress is True
    assert "Exported database to /tmp/export.sql.gz" in stdout.getvalue()


@override_settings(PTECH_TOOLS={"EXPORT_DB": {"compress": True}})
def test_export_db_command_can_disable_compress_with_flag(monkeypatch):
    captured = {}

    class DummyService:
        def __init__(self, config, *, connection=None, runner=None, clock=None):
            captured["config"] = config

        def export(self):
            return Path("/tmp/export.sql")

    monkeypatch.setattr(export_db_command, "ExportDBService", DummyService)

    stdout = StringIO()
    call_command("export_db", compress=False, stdout=stdout)

    assert captured["config"].compress is False
    assert "Exported database to /tmp/export.sql" in stdout.getvalue()
