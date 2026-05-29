from pathlib import Path

from django.test import override_settings

from ptech_tools.conf import load_export_db_config


def test_load_export_db_config_uses_defaults():
    config = load_export_db_config()

    assert config.database_alias == "default"
    assert config.output_dir == Path("backups")
    assert config.filename_template == "{database_alias}_{timestamp}.sql"
    assert config.engine == "auto"
    assert config.compress is False
    assert config.include_tables == ()
    assert config.exclude_tables == ()


@override_settings(
    PTECH_TOOLS={
        "EXPORT_DB": {
            "database_alias": "analytics",
            "output_dir": Path("/tmp/ptech-backups"),
            "compress": True,
            "include_tables": ["users", "orders"],
            "exclude_tables": ("audit_log",),
        }
    }
)
def test_load_export_db_config_uses_django_settings():
    config = load_export_db_config()

    assert config.database_alias == "analytics"
    assert config.output_dir == Path("/tmp/ptech-backups")
    assert config.compress is True
    assert config.include_tables == ("users", "orders")
    assert config.exclude_tables == ("audit_log",)


@override_settings(PTECH_TOOLS={"EXPORT_DB": {"output_dir": Path("/from-settings")}})
def test_load_export_db_config_prefers_env_over_settings(monkeypatch):
    monkeypatch.setenv("PTECH_TOOLS_EXPORT_DB_OUTPUT_DIR", "/from-env")
    monkeypatch.setenv("PTECH_TOOLS_EXPORT_DB_INCLUDE_TABLES", "users, orders")
    monkeypatch.setenv("PTECH_TOOLS_EXPORT_DB_EXCLUDE_TABLES", "audit_log, sessions")
    monkeypatch.setenv("PTECH_TOOLS_EXPORT_DB_COMPRESS", "true")

    config = load_export_db_config()

    assert config.output_dir == Path("/from-env")
    assert config.include_tables == ("users", "orders")
    assert config.exclude_tables == ("audit_log", "sessions")
    assert config.compress is True
