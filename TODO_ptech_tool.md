# TODO - `ptech-tools`

Objetivo: transformar rotinas reutilizaveis em um pacote Django/Python instalavel e compartilhaveis entre projetos, sem duplicar logica em cada repositorio.

## Decisao ja tomada

- O pacote vai se chamar `ptech-tools`.
- Ele deve ser instalavel via `pip`.
- Ele deve funcionar como app Django, para poder ser ativado com `INSTALLED_APPS`.
- A ideia e publicar no PyPI, porque nao ha conteudo privado a principio.

## Escopo inicial sugerido

- Extrair o comando `export_db`.
- Manter a logica comum do backup centralizada no pacote.
- Deixar cada projeto com configuracao local minima.
- Permitir comportamento por `settings` e variaveis de ambiente.

## Estrutura desejada

- `pyproject.toml`
- `src/ptech_tool/`
- `src/ptech_tool/apps.py`
- `src/ptech_tool/management/commands/export_db.py`
- `src/ptech_tool/services/`
- `tests/`

## Passos futuros

- Criar o repositorio novo do pacote.
- Definir a estrutura do projeto com `src layout`.
- Mover a logica do backup para o pacote.
- Criar testes proprios do pacote.
- Publicar uma primeira versao no PyPI.
- Consumir o pacote nos projetos atuais com `pip install ptech-tools`.
- Adicionar `ptech_tool` em `INSTALLED_APPS`.

## Regras de projeto

- Evitar nomes amarrados a um sistema especifico.
- Evitar depender de codigo-fonte copiado entre repositorios.
- Manter a interface de uso simples para os projetos consumidores.
- Preferir configuracao por ambiente em vez de valores fixos.

## Pontos para retomar depois

- Quais comandos entram na primeira versao alem de `export_db`.
- Quais configuracoes serao obrigatorias e quais serao opcionais.
- Se o pacote tera uma API de servico alem dos commands Django.
- Qual fluxo de publicacao sera usado para o PyPI.
