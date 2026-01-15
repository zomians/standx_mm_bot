.PHONY: run test typecheck lint format check install clean

# Bot起動
run:
	python -m standx_mm_bot

# テスト実行
test:
	pytest

# テスト (カバレッジ付き)
test-cov:
	pytest --cov --cov-report=term-missing

# 型チェック
typecheck:
	mypy src

# Lint
lint:
	ruff check src tests

# フォーマット
format:
	ruff format src tests
	ruff check --fix src tests

# 全チェック (lint + typecheck + test)
check: lint typecheck test

# 依存関係インストール
install:
	pip install -e ".[dev]"

# キャッシュ削除
clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
