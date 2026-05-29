# ptech-tools

Pacote reutilizavel de utilitarios Django/Python para os projetos da PTech.

## Instalacao

```bash
pip install ptech-tools
```

Requer Django 5.2 ou superior.

## Uso no Django

Adicione o app em `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "ptech_tools.apps.PtechToolsConfig",
]
```

## Comando inicial

O pacote ja expoe o comando `export_db`:

```bash
python manage.py export_db
```

Configuracao opcional via `settings.py`:

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

PTECH_TOOLS = {
    "EXPORT_DB": {
        "output_dir": BASE_DIR / "backups",
        "database_alias": "default",
        "compress": True,
        "include_tables": ["users", "orders"],
        "exclude_tables": ["audit_log"],
    }
}
```

O comando tambem aceita flags diretas:

```bash
python manage.py export_db --compress --include-table users --include-table orders
```

Quando `compress=True` ou `--compress` estiver ativo, o arquivo final termina em `.gz`.
Use `--no-compress` para forcar saida sem compactacao, mesmo se `compress=True` estiver configurado.

`include_tables` e `exclude_tables` aceitam listas no `settings.py` e valores separados por virgula nas variaveis de ambiente.

## Publicacao

O fluxo de publicacao para TestPyPI e PyPI esta documentado em [docs/publishing.md](docs/publishing.md).
