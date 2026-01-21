.PHONY: up down test test-cov typecheck lint format format-check check logs clean build-prod up-prod restart-prod wallet price orders position balance status switch-eth switch-btc up-eth up-btc config

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

# フォーマットチェック（修正なし）
format-check:
	docker compose run --rm bot ruff format --check src tests

# 全チェック (format-check + lint + typecheck + test-cov)
check: format-check lint typecheck test-cov

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

# ウォレット作成と.env生成
wallet:
	@echo "Creating new Solana wallet and generating .env file..."
	docker compose run --rm bot python scripts/create_wallet.py

# API読み取りコマンド（動作確認・デバッグ用）
price:
	@echo "Fetching current price..."
	docker compose run --rm bot python scripts/read_api.py price

orders:
	@echo "Fetching open orders..."
	docker compose run --rm bot python scripts/read_api.py orders

position:
	@echo "Fetching current position..."
	docker compose run --rm bot python scripts/read_api.py position

balance:
	@echo "Fetching balance (StandX + Solana)..."
	docker compose run --rm bot python scripts/read_api.py balance

status:
	@echo "Fetching all status..."
	docker compose run --rm bot python scripts/read_api.py status

# シンボル切り替え: ETH-USD
switch-eth:
	@if [ ! -f .env ]; then echo "Error: .env file not found. Run 'cp .env.example .env' first."; exit 1; fi
	@sed -i.bak 's/^SYMBOL=.*/SYMBOL=ETH-USD/' .env && rm -f .env.bak
	@echo "✅ Switched to ETH-USD"
	@grep "^SYMBOL=" .env

# シンボル切り替え: BTC-USD
switch-btc:
	@if [ ! -f .env ]; then echo "Error: .env file not found. Run 'cp .env.example .env' first."; exit 1; fi
	@sed -i.bak 's/^SYMBOL=.*/SYMBOL=BTC-USD/' .env && rm -f .env.bak
	@echo "✅ Switched to BTC-USD"
	@grep "^SYMBOL=" .env

# ETH-USDで起動
up-eth: switch-eth up

# BTC-USDで起動
up-btc: switch-btc up

# 現在の設定確認（秘密鍵・アドレスは表示しない）
config:
	@echo "=== Current Configuration ==="
	@if [ -f .env ]; then \
		cat .env | grep -v "PRIVATE_KEY\|WALLET_ADDRESS" | grep -v "^#" | grep -v "^$$"; \
	else \
		echo "Error: .env file not found"; \
	fi
