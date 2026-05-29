from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from ptech_tools.conf import load_export_db_config
from ptech_tools.services import ExportDBService


class Command(BaseCommand):
    help = "Exporta o banco de dados configurado no projeto."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--database", default=None, help="Alias do banco no Django.")
        parser.add_argument("--output-dir", default=None, help="Diretorio de destino do backup.")
        parser.add_argument(
            "--filename-template",
            default=None,
            help="Template do nome do arquivo, por exemplo '{database_alias}_{timestamp}.sql'.",
        )
        parser.add_argument(
            "--timestamp-format",
            default=None,
            help="Formato do timestamp usado no nome do arquivo.",
        )
        parser.add_argument(
            "--engine",
            default=None,
            help="Forca o backend: auto, sqlite, postgres ou mysql.",
        )
        parser.add_argument("--pg-dump-path", default=None, help="Caminho para o executavel pg_dump.")
        parser.add_argument(
            "--mysqldump-path",
            default=None,
            help="Caminho para o executavel mysqldump.",
        )
        compression_group = parser.add_mutually_exclusive_group()
        compression_group.add_argument(
            "--compress",
            dest="compress",
            action="store_true",
            default=None,
            help="Gera um arquivo .gz com o resultado final.",
        )
        compression_group.add_argument(
            "--no-compress",
            dest="compress",
            action="store_false",
            help="Desativa a compressao, mesmo se estiver habilitada nas configuracoes.",
        )
        parser.add_argument(
            "--include-table",
            dest="include_tables",
            action="append",
            default=None,
            help="Inclui uma tabela especifica no dump. Pode ser repetido.",
        )
        parser.add_argument(
            "--exclude-table",
            dest="exclude_tables",
            action="append",
            default=None,
            help="Exclui uma tabela especifica do dump. Pode ser repetido.",
        )
        parser.add_argument("--dry-run", action="store_true", help="Mostra o caminho sem exportar.")

    def handle(self, *args, **options):
        config = load_export_db_config(
            {
                "database_alias": options["database"],
                "output_dir": options["output_dir"],
                "filename_template": options["filename_template"],
                "timestamp_format": options["timestamp_format"],
                "engine": options["engine"],
                "pg_dump_path": options["pg_dump_path"],
                "mysqldump_path": options["mysqldump_path"],
                "include_tables": options["include_tables"],
                "exclude_tables": options["exclude_tables"],
                "compress": options["compress"],
            }
        )

        service = ExportDBService(config)
        if options["dry_run"]:
            target = service.build_target_path()
            self.stdout.write(str(target))
            return

        try:
            target = service.export()
        except Exception as exc:  # pragma: no cover - command boundary
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(f"Exported database to {target}"))
        return
