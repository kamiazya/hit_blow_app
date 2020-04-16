# Hit & Blow App

## Commands

- インストール

```sh
poetry install
```

- 仮想環境に入る

```sh
poetry shell
```

- 開発用コマンド

```sh
uvicorn src.hit_blow_app.main:app --reload
```

- 静的解析系

```sh
# Lint
poetry run flake8 --show-source .
poetry run poetry run black . --check
poetry run isort -rc -sl -c .
# TypeCheck
poetry run mypy
# Format
poetry run autopep8 -ivr .
poetry run black .
poetry run isort -rc -sl .
```
