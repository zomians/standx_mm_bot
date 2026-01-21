# Phase 1-1: 設定管理とデータモデルの実装ガイド

このドキュメントは、Issue #12「Phase 1-1: 設定管理とデータモデルの実装」で実装した内容を、初心者向けに詳しく解説します。

---

## 📋 目次

1. [概要](#概要)
2. [実装したファイル](#実装したファイル)
3. [pydantic-settingsの基礎](#pydantic-settingsの基礎)
4. [config.pyの実装解説](#configpyの実装解説)
5. [models.pyの実装解説](#modelspyの実装解説)
6. [テストの書き方](#テストの書き方)
7. [Docker環境での開発フロー](#docker環境での開発フロー)
8. [よくあるエラーと対処法](#よくあるエラーと対処法)

---

## 概要

### 何を実装したか

Phase 1-1では、Bot開発の基盤となる**設定管理**と**データモデル**を実装しました。

| ファイル | 役割 |
|---------|------|
| `config.py` | 環境変数から設定を読み込み、型安全に管理 |
| `models.py` | データ構造（注文、ポジション等）を定義 |
| `.env.example` | 環境変数のテンプレート |
| `test_config.py` | config.pyのテスト |
| `test_models.py` | models.pyのテスト |

### なぜ重要か

- **型安全性**: 設定ミスを実行前に検出
- **バリデーション**: 不正な値を自動でチェック
- **保守性**: データ構造が明確で、変更が容易

---

## 実装したファイル

### ディレクトリ構成

```
standx_mm_bot/
├── src/standx_mm_bot/
│   ├── __init__.py          # パッケージ初期化
│   ├── config.py            # 設定管理
│   └── models.py            # データモデル
├── tests/
│   ├── __init__.py
│   ├── test_config.py       # config.pyのテスト
│   └── test_models.py       # models.pyのテスト
└── .env.example             # 環境変数テンプレート
```

---

## pydantic-settingsの基礎

### pydantic-settingsとは

[pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)は、環境変数から設定を読み込み、型チェックとバリデーションを行うライブラリです。

### 基本的な使い方

```python
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 環境変数 API_KEY を読み込む
    api_key: str = Field(..., description="APIキー")
    
    # デフォルト値付き
    timeout: int = Field(30, description="タイムアウト(秒)")
    
    # .envファイルから読み込む設定
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }
```

### 環境変数の命名規則

pydantic-settingsは、**大文字**の環境変数を自動的にマッピングします。

| Pythonフィールド名 | 環境変数名 |
|-------------------|-----------|
| `api_key` | `API_KEY` |
| `standx_private_key` | `STANDX_PRIVATE_KEY` |
| `target_distance_bps` | `TARGET_DISTANCE_BPS` |

---

## config.pyの実装解説

### 全体構造

```python
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 必須フィールド（デフォルト値なし）
    standx_private_key: str = Field(..., description="ウォレット秘密鍵")
    
    # オプションフィールド（デフォルト値あり）
    symbol: str = Field("ETH_USDC", description="取引ペア")
    
    # バリデーション
    @field_validator("target_distance_bps")
    @classmethod
    def validate_target_distance(cls, v: float) -> float:
        if not 0 < v < 10:
            raise ValueError("target_distance_bps must be between 0 and 10")
        return v
    
    # 設定
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }
```

### 重要なポイント

#### 1. 必須フィールドとオプションフィールド

```python
# 必須: デフォルト値を ... にする
standx_private_key: str = Field(..., description="ウォレット秘密鍵")

# オプション: デフォルト値を指定
symbol: str = Field("ETH_USDC", description="取引ペア")
```

**理由**: 秘密鍵などの重要な値は、環境変数で必ず設定させるため。

#### 2. field_validatorによるバリデーション

```python
@field_validator("target_distance_bps")
@classmethod
def validate_target_distance(cls, v: float) -> float:
    if not 0 < v < 10:
        raise ValueError("target_distance_bps must be between 0 and 10")
    return v
```

**使い方**:
- `@field_validator("フィールド名")` で対象フィールドを指定
- `@classmethod` デコレータが必須
- `v` が検証する値、戻り値が最終的な値

**メリット**:
- 設定ミスを実行前に検出
- エラーメッセージでユーザーに通知

#### 3. pydantic v2の設定方法

```python
# pydantic v2では model_config を使う
model_config = {
    "env_file": ".env",
    "env_file_encoding": "utf-8",
}
```

**pydantic v1との違い**:
```python
# v1（古い書き方）
class Config:
    env_file = ".env"

# v2（新しい書き方）
model_config = {"env_file": ".env"}
```

### 設定の使い方

```python
from standx_mm_bot.config import Settings

# 設定を読み込む
settings = Settings()

# 値にアクセス
print(settings.symbol)  # "ETH_USDC"
print(settings.target_distance_bps)  # 8.0
```

---

## models.pyの実装解説

### なぜdataclassを使うのか

**dataclass**は、データを保持するだけのクラスを簡潔に書けるPythonの機能です。

```python
# dataclassなし（冗長）
class Order:
    def __init__(self, id: str, price: float, size: float):
        self.id = id
        self.price = price
        self.size = size

# dataclassあり（簡潔）
@dataclass
class Order:
    id: str
    price: float
    size: float
```

### Enumの実装

```python
from enum import Enum

class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
```

**使い方**:
```python
# 列挙型として使う
order_side = Side.BUY

# 文字列として使う（str, Enumを継承しているため）
print(order_side)  # "BUY"
api_call(side=order_side)  # API呼び出しで文字列として送信可能
```

**メリット**:
- タイポを防止（`"BUUY"` のようなミスを防ぐ）
- IDEの補完が効く
- 型チェックで検出可能

### dataclassのデフォルト値

```python
@dataclass
class Order:
    id: str
    price: float
    size: float
    filled_size: float = 0.0  # デフォルト値
    timestamp: datetime | None = None  # Optionalなフィールド
```

**使い方**:
```python
# デフォルト値を使う
order = Order(id="123", price=2000.0, size=0.1)
print(order.filled_size)  # 0.0

# 明示的に指定
order = Order(
    id="123",
    price=2000.0,
    size=0.1,
    filled_size=0.05,
    timestamp=datetime.now()
)
```

### Union型（Python 3.10+）

```python
# Python 3.10以降の書き方
timestamp: datetime | None = None

# Python 3.9以前の書き方
from typing import Optional
timestamp: Optional[datetime] = None
```

---

## テストの書き方

### test_config.pyのポイント

#### 1. 一時ファイルを使ったテスト

```python
def test_settings_with_env_file(tmp_path: Path) -> None:
    """環境変数ファイルから設定を読み込めることを確認."""
    # 一時的な.envファイルを作成
    env_file = tmp_path / ".env"
    env_file.write_text(
        "STANDX_PRIVATE_KEY=0x1234567890abcdef\n"
        "STANDX_WALLET_ADDRESS=0xabcdef1234567890\n"
    )
    
    # 一時ファイルを指定して読み込み
    settings = Settings(_env_file=str(env_file))
    
    assert settings.standx_private_key == "0x1234567890abcdef"
```

**tmp_path**: pytestが自動的に提供する一時ディレクトリ。テスト終了後に自動削除される。

#### 2. 環境変数のクリーンアップ

```python
def test_settings_default_values() -> None:
    # 環境変数を設定
    os.environ["STANDX_PRIVATE_KEY"] = "0xtest"
    
    settings = Settings()
    
    # テスト後にクリーンアップ（重要！）
    del os.environ["STANDX_PRIVATE_KEY"]
```

**理由**: 環境変数が残ると、他のテストに影響を与える可能性がある。

#### 3. バリデーションエラーのテスト

```python
def test_settings_validation_target_distance_too_small() -> None:
    os.environ["TARGET_DISTANCE_BPS"] = "-1.0"
    
    # エラーが発生することを確認
    with pytest.raises(ValidationError) as exc_info:
        Settings()
    
    # エラーメッセージを確認
    assert "target_distance_bps must be between 0 and 10" in str(exc_info.value)
```

### test_models.pyのポイント

#### Enumのテスト

```python
def test_side_enum() -> None:
    """Side Enumの値が正しいことを確認."""
    assert Side.BUY == "BUY"
    assert Side.SELL == "SELL"
```

**なぜ必要？**: Enumの値を変更したときに、他の部分に影響がないか確認するため。

#### dataclassのテスト

```python
def test_order_creation() -> None:
    """Orderインスタンスが正しく作成されることを確認."""
    order = Order(
        id="order_123",
        symbol="ETH_USDC",
        side=Side.BUY,
        price=2000.0,
        size=0.1,
        order_type=OrderType.LIMIT,
        status=OrderStatus.OPEN,
    )
    
    assert order.id == "order_123"
    assert order.side == Side.BUY
```

---

## Docker環境での開発フロー

### 基本的な流れ

```bash
# 1. コードを編集
vim src/standx_mm_bot/config.py

# 2. テスト実行
make test

# 3. 型チェック
make typecheck

# 4. Lintチェック
make lint

# 5. 全チェック
make check
```

### Docker環境のポイント

#### PYTHONPATH設定

`compose.yaml`で`PYTHONPATH`を設定しているため、Dockerコンテナ内で`standx_mm_bot`モジュールをimportできます。

```yaml
services:
  bot:
    environment:
      - PYTHONPATH=/app/src
```

**理由**: `/app/src/standx_mm_bot/`にあるモジュールを、`from standx_mm_bot import ...`でimportするため。

#### ボリュームマウント

```yaml
volumes:
  - ./src:/app/src:ro
  - ./tests:/app/tests:ro
```

**メリット**:
- ホストで編集したファイルが即座にコンテナに反映
- `:ro`（read-only）でコンテナからの変更を防止

#### イメージの再ビルドが必要なケース

```bash
# 依存関係を変更した場合
vim pyproject.toml
docker compose build bot

# ソースコードのみ変更した場合（再ビルド不要）
vim src/standx_mm_bot/config.py
make test  # そのまま実行可能
```

---

## よくあるエラーと対処法

### 1. ModuleNotFoundError: No module named 'standx_mm_bot'

**原因**: PYTHONPATHが設定されていない

**対処法**:
```bash
# compose.yamlに以下を追加
environment:
  - PYTHONPATH=/app/src
```

### 2. ValidationError: field required

**原因**: 必須の環境変数が設定されていない

**対処法**:
```bash
# .envファイルを作成
cp .env.example .env

# 必須フィールドを設定
vim .env
```

### 3. ValueError: target_distance_bps must be between 0 and 10

**原因**: バリデーションエラー（範囲外の値）

**対処法**:
```bash
# .envファイルで正しい値を設定
TARGET_DISTANCE_BPS=8.0
```

### 4. テストで環境変数が残る

**原因**: テスト後のクリーンアップ漏れ

**対処法**:
```python
def test_something() -> None:
    os.environ["KEY"] = "value"
    
    # ... テスト ...
    
    # 必ずクリーンアップ
    del os.environ["KEY"]
```

---

## まとめ

Phase 1-1では以下を実装しました：

✅ **config.py**: pydantic-settingsで型安全な設定管理  
✅ **models.py**: Enumとdataclassでデータモデル定義  
✅ **.env.example**: 環境変数テンプレート  
✅ **テスト**: 15件のユニットテスト  
✅ **Docker環境**: PYTHONPATH設定とボリュームマウント

### 次のステップ

Phase 1-2では、JWT認証（auth.py）を実装します。

- [Issue #13: Phase 1-2: JWT認証の実装](https://github.com/zomians/standx_mm_bot/issues/13)

---

## 参考資料

- [pydantic-settings公式ドキュメント](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Python dataclass公式ドキュメント](https://docs.python.org/ja/3/library/dataclasses.html)
- [pytest公式ドキュメント](https://docs.pytest.org/)
