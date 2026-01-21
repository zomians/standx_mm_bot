# ===== Base Stage =====
FROM python:3.12-slim as base
WORKDIR /app

# システムパッケージ更新
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ===== Development Stage =====
FROM base as dev

# 依存関係ファイルをコピー
COPY pyproject.toml README.md ./

# 開発用依存関係をインストール
RUN pip install --no-cache-dir -e ".[dev]"

# ソースコードをコピー
COPY . .

# 非rootユーザー作成
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

CMD ["python", "-m", "standx_mm_bot"]

# ===== Production Stage =====
FROM base as prod

# 依存関係ファイルをコピー
COPY pyproject.toml README.md ./

# 本番用依存関係のみインストール
RUN pip install --no-cache-dir .

# ソースコードをコピー
COPY src/ ./src/

# 非rootユーザー作成
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

CMD ["python", "-m", "standx_mm_bot"]
