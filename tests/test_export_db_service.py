from datetime import datetime
import gzip
import sqlite3

from ptech_tools.conf import ExportDBConfig
from ptech_tools.services import ExportDBService


class FakeConnection:
    def __init__(
        self,
        raw_connection=None,
        *,
        engine="django.db.backends.sqlite3",
        name=":memory:",
        host="",
        port="",
        user="",
        password="",
    ) -> None:
        self._raw_connection = raw_connection
        self.settings_dict = {"ENGINE": engine, "NAME": name}
        if host:
            self.settings_dict["HOST"] = host
        if port:
            self.settings_dict["PORT"] = port
        if user:
            self.settings_dict["USER"] = user
        if password:
            self.settings_dict["PASSWORD"] = password

    def ensure_connection(self) -> None:
        return None

    @property
    def connection(self):
        return self._raw_connection


def test_export_db_service_exports_sqlite_dump(tmp_path):
    raw_connection = sqlite3.connect(":memory:")
    raw_connection.execute("create table example (id integer primary key, name text not null)")
    raw_connection.execute("insert into example (name) values (?)", ("alpha",))
    raw_connection.commit()

    service = ExportDBService(
        ExportDBConfig(output_dir=tmp_path),
        connection=FakeConnection(raw_connection),
        clock=lambda: datetime(2026, 1, 2, 3, 4, 5),
    )

    target = service.export()

    assert target.exists()
    assert target.name == "default_20260102_030405.sql"
    content = target.read_text(encoding="utf-8")
    assert "example" in content
    assert "INSERT INTO" in content


def test_export_db_service_filters_sqlite_dump_and_compresses(tmp_path):
    raw_connection = sqlite3.connect(":memory:")
    raw_connection.execute("create table keep_me (id integer primary key, name text not null)")
    raw_connection.execute("create table drop_me (id integer primary key, name text not null)")
    raw_connection.execute("insert into keep_me (name) values (?)", ("alpha",))
    raw_connection.execute("insert into drop_me (name) values (?)", ("beta",))
    raw_connection.commit()

    service = ExportDBService(
        ExportDBConfig(output_dir=tmp_path, compress=True, include_tables=("keep_me",)),
        connection=FakeConnection(raw_connection),
        clock=lambda: datetime(2026, 1, 2, 3, 4, 5),
    )

    target = service.export()

    assert target.exists()
    assert target.name == "default_20260102_030405.sql.gz"
    with gzip.open(target, "rt", encoding="utf-8") as handle:
        content = handle.read()
    assert "keep_me" in content
    assert "drop_me" not in content


def test_build_target_path_uses_template(tmp_path):
    service = ExportDBService(
        ExportDBConfig(
            output_dir=tmp_path,
            filename_template="{database_alias}-{timestamp}.sql",
        ),
        clock=lambda: datetime(2026, 5, 29, 10, 11, 12),
    )

    assert service.build_target_path().name == "default-20260529_101112.sql"


def test_build_target_path_adds_gz_suffix_when_compressing(tmp_path):
    service = ExportDBService(
        ExportDBConfig(
            output_dir=tmp_path,
            filename_template="{database_alias}-{timestamp}.sql",
            compress=True,
        ),
        clock=lambda: datetime(2026, 5, 29, 10, 11, 12),
    )

    assert service.build_target_path().name == "default-20260529_101112.sql.gz"


def test_export_db_service_builds_postgres_command(tmp_path):
    captured = {}

    def runner(command, check, env, stdout):
        captured["command"] = command
        captured["env"] = env
        stdout.write(b"PGDUMP\n")

    service = ExportDBService(
        ExportDBConfig(
            output_dir=tmp_path,
            include_tables=("users", "orders"),
            exclude_tables=("audit_log",),
        ),
        connection=FakeConnection(
            engine="django.db.backends.postgresql",
            name="inventory",
            host="db.example",
            port="5432",
            user="alice",
            password="secret",
        ),
        runner=runner,
        clock=lambda: datetime(2026, 5, 29, 10, 11, 12),
    )

    target = service.export()

    assert target.read_bytes() == b"PGDUMP\n"
    assert captured["env"]["PGPASSWORD"] == "secret"
    assert captured["command"][0] == "pg_dump"
    assert "--host" in captured["command"]
    assert "--port" in captured["command"]
    assert "--username" in captured["command"]
    assert "--table=users" in captured["command"]
    assert "--table=orders" in captured["command"]
    assert "--exclude-table=audit_log" in captured["command"]
    assert captured["command"][-1] == "inventory"


def test_export_db_service_builds_mysql_command(tmp_path):
    captured = {}

    def runner(command, check, env, stdout):
        captured["command"] = command
        captured["env"] = env
        stdout.write(b"MYSQLDUMP\n")

    service = ExportDBService(
        ExportDBConfig(
            output_dir=tmp_path,
            include_tables=("users", "orders"),
            exclude_tables=("audit_log",),
        ),
        connection=FakeConnection(
            engine="django.db.backends.mysql",
            name="inventory",
            host="db.example",
            port="3306",
            user="alice",
            password="secret",
        ),
        runner=runner,
        clock=lambda: datetime(2026, 5, 29, 10, 11, 12),
    )

    target = service.export()

    assert target.read_bytes() == b"MYSQLDUMP\n"
    assert captured["env"]["MYSQL_PWD"] == "secret"
    assert captured["command"][0] == "mysqldump"
    assert "--single-transaction" in captured["command"]
    assert "--quick" in captured["command"]
    assert "--skip-lock-tables" in captured["command"]
    assert "--routines" in captured["command"]
    assert "--triggers" in captured["command"]
    assert "--events" in captured["command"]
    assert "--ignore-table=inventory.audit_log" in captured["command"]
    assert captured["command"][-3:] == ["inventory", "users", "orders"]
