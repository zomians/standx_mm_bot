.PHONY: up down test test-cov typecheck lint format check logs clean build-prod up-prod restart-prod

# 開発環境: Bot起動
up:
	docker compose up -d

# 開発環境: Bot停止
down:
	docker compose down

# テスト実行
test:
	docker compose run --rm bot pytest

# テスト (カバレッジ付き)
test-cov:
	docker compose run --rm bot pytest --cov --cov-report=term-missing

# 型チェック
typecheck:
	docker compose run --rm bot mypy src

# Lint
lint:
	docker compose run --rm bot ruff check src tests

# フォーマット
format:
	docker compose run --rm bot ruff format src tests
	docker compose run --rm bot ruff check --fix src tests

# 全チェック (lint + typecheck + test)
check: lint typecheck test

# ログ確認
logs:
	docker compose logs -f bot

# クリーンアップ
clean:
	docker compose down -v
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# 本番環境: イメージビルド
build-prod:
	docker compose -f compose.prod.yaml build

# 本番環境: Bot起動
up-prod:
	docker compose -f compose.prod.yaml up -d

# 本番環境: Bot再起動
restart-prod:
	docker compose -f compose.prod.yaml restart
