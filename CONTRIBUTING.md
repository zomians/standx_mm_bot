# 開発ガイド

StandX MM Bot プロジェクトへようこそ！このガイドでは、プロジェクトへの貢献方法と開発ワークフローを説明します。

---

## ドキュメント役割分担

各ドキュメントの役割を明確に分離し、情報の重複を避けています。

| コンテンツ               | README.md | CONTRIBUTING.md | CLAUDE.md |
| ------------------------ | :-------: | :-------------: | :-------: |
| **プロジェクト概要**     |     ◎     |        −        |     ○     |
| **技術スタック**         |     ◎     |        −        |     ○     |
| **クイックスタート**     |     ◎     |        −        |     ○     |
| **ディレクトリ構成**     |     ◎     |        −        |     ○     |
| **よく使うコマンド**     |     ◎     |        −        |     ◎     |
| **トラブルシューティング** |     ◎     |        −        |     ○     |
| **ドキュメント役割分担** |     −     |        ◎        |     ○     |
| **Issue 作成ガイド**     |     −     |        ◎        |     ○     |
| **Git ワークフロー**     |     −     |        ◎        |     ○     |
| **コミット規約**         |     −     |        ◎        |     ○     |
| **PR 作成フロー**        |     −     |        ◎        |     ○     |
| **コーディング規約**     |     −     |        ◎        |     −     |
| **テスト方針**           |     −     |        ◎        |     −     |
| **コードレビュー基準**   |     −     |        ◎        |     −     |
| **セキュリティチェック** |     −     |        ◎        |     ○     |

**凡例**: ◎ 詳細に記載 / ○ 簡潔に記載・参照 / − 含まない

---

## 目次

- [Issue 作成ガイドライン](#issue-作成ガイドライン)
- [Git ワークフロー](#git-ワークフロー)
- [コミット規約](#コミット規約)
- [PR 作成フロー](#pr作成フロー)
- [コーディング規約](#コーディング規約)
- [テスト方針](#テスト方針)
- [コードレビュー基準](#コードレビュー基準)

---

## Issue 作成ガイドライン

新機能開発やバグ修正を行う前に、必ず GitHub Issue を作成してください。Issue は実装の設計書であり、レビューの基準となります。

### Issue テンプレート

以下のテンプレートに沿って Issue を作成してください：

```markdown
## 概要

[1-2文で変更内容を簡潔に説明]

**関連issue**: [関連するIssue番号があれば記載]

---

## 背景・課題

### 現状の問題
- [現在どのような問題があるか]
- [なぜこの変更が必要なのか]

### 課題
- [具体的な課題1]
- [具体的な課題2]

---

## 目的・ゴール

### 主目的
[この変更で達成したいこと]

### 副次的目標
- [追加で達成したいこと1]
- [追加で達成したいこと2]

---

## 要件定義

### 機能要件

#### FR-1: [機能名1]
- [詳細な要件説明]
- [実装内容]

### 非機能要件

#### NFR-1: パフォーマンス
- [パフォーマンス要件]

#### NFR-2: セキュリティ
- [セキュリティ要件]

---

## 技術仕様

### 実装詳細

[具体的な実装方法、コード例など]

---

## 受け入れ基準

### 必須（Must Have）
- [ ] [必須要件1]
- [ ] [必須要件2]

### 推奨（Should Have）
- [ ] [推奨要件1]

---

## テスト計画

### テストケース

#### TC-1: [テストケース名1]
- **手順**: [手順]
- **期待結果**: [期待される結果]

---

## Definition of Done

- [ ] すべてのテストケース合格
- [ ] コードレビュー承認
- [ ] ドキュメント更新完了

---

**優先度**: High/Medium/Low
**難易度**: High/Medium/Low
```

### 優先度と難易度の定義

#### 優先度（Priority）

| レベル | 説明 | 例 |
|--------|------|-----|
| **High** | 本番運用に必須、ブロッカー | セキュリティ修正、重大なバグ修正 |
| **Medium** | 重要だが緊急ではない | 新機能、パフォーマンス改善 |
| **Low** | あると良い、将来的に対応 | リファクタリング、ドキュメント追加 |

#### 難易度（Difficulty）

| レベル | 説明 |
|--------|------|
| **Low** | 単純な変更、影響範囲が小さい |
| **Medium** | 複数ファイルの変更、設計が必要 |
| **High** | アーキテクチャ変更、複数モジュール横断 |

---

## Git ワークフロー

このプロジェクトは **[GitHub Flow](https://docs.github.com/ja/get-started/quickstart/github-flow)** を採用しています。

### 重要な原則：ブランチを作ってから作業する

**作業を開始する前に、必ず以下の手順を守ってください：**

1. **main ブランチで直接作業しない**
   ```bash
   # BAD: main ブランチで直接編集
   git checkout main
   vim some_file.py  # 危険！
   ```

2. **Issue 作成 → ブランチ作成 → 実装の順序を守る**
   ```bash
   # GOOD: 正しい手順
   # Step 1: Issue 作成（GitHub で実施）
   # Step 2: main を最新化
   git checkout main
   git pull origin main

   # Step 3: 新しいブランチを作成
   git checkout -b feature/12-websocket-connection

   # Step 4: 実装開始
   vim some_file.py
   ```

### 基本フロー

```
1. Issue作成 → 2. ブランチ作成 → 3. 実装 → 4. PR作成 → 5. レビュー → 6. マージ
```

### ブランチ戦略

#### ブランチ命名規則

```
<type>/<issue番号>-<機能名>
```

**Type 一覧**:

- `feature/` - 新機能開発
- `bugfix/` - バグ修正
- `hotfix/` - 緊急修正
- `refactor/` - リファクタリング
- `docs/` - ドキュメント変更

**例**:

```bash
feature/1-authentication
feature/2-order-management
bugfix/3-fix-reconnection
hotfix/4-api-key-leak
refactor/5-cleanup-websocket
docs/6-update-readme
```

#### 保護ブランチ

- **main**: 本番環境用（直接プッシュ禁止、PR 経由のみ）

---

## コミット規約

### Conventional Commits 準拠

**フォーマット**:

```
<type>(<scope>): <subject> (issue#<番号>)

<body>（オプション）

<footer>（オプション）
```

### Type 一覧

| Type       | 説明               | 例                                        |
| ---------- | ------------------ | ----------------------------------------- |
| `feat`     | 新機能             | `feat(ws): WebSocket接続を実装`           |
| `fix`      | バグ修正           | `fix(order): 再発注ロジックを修正`        |
| `docs`     | ドキュメント       | `docs: CONTRIBUTING.mdを追加`             |
| `refactor` | リファクタリング   | `refactor(core): 注文管理構造を整理`      |
| `test`     | テスト追加・修正   | `test(auth): 認証フローのテストを追加`    |
| `chore`    | ビルド・ツール設定 | `chore: pyproject.tomlを更新`             |
| `perf`     | パフォーマンス改善 | `perf(ws): メッセージ処理を最適化`        |
| `style`    | コードスタイル     | `style: フォーマット修正`                 |

### Scope 一覧（オプション）

- `auth` - 認証関連
- `ws` - WebSocket関連
- `order` - 注文管理
- `position` - ポジション管理
- `risk` - リスク制御
- `config` - 設定関連
- `docs` - ドキュメント

### 良いコミットメッセージの例

```bash
# GOOD
feat(auth): JWT認証フローを実装 (issue#1)
feat(ws): WebSocket接続・再接続を実装 (issue#2)
fix(order): 注文キャンセル後の再発注タイミングを修正 (issue#3)
docs: READMEを追加 (issue#4)
test(order): 注文管理のユニットテストを追加 (issue#5)
```

### 悪いコミットメッセージの例

```bash
# BAD
update
fix bug
WIP
修正
```

### コミット時の注意事項

1. **1 コミット 1 機能**: 関連する変更のみを含める
2. **意味のある単位**: 「WIP」コミットは避ける
3. **日本語 OK**: subject は日本語で明確に
4. **Issue 番号必須**: `(issue#XX)` を必ず含める

---

## PR 作成フロー

### 1. 実装とコミット

```bash
# 実装
# ...

# ステージング
git add .

# コミット
git commit -m "feat(ws): WebSocket接続を実装 (issue#2)"

# プッシュ
git push origin feature/2-websocket-connection
```

### 2. PR 作成

```bash
# GitHub CLIでPR作成
gh pr create --title "WebSocket接続を実装" --body "$(cat <<'EOF'
## 概要
issue#2のWebSocket接続機能を実装しました。

## 変更内容
- WebSocket接続・認証
- 自動再接続ロジック
- price/orderチャンネル購読

## テスト方法
```bash
python -m pytest tests/test_websocket.py
```

## チェックリスト

- [x] テスト追加
- [x] 型チェック通過
- [x] ドキュメント更新

Closes #2
EOF
)"
```

### 3. PR テンプレート

PR には以下を含めてください：

```markdown
## 概要

[変更の概要を 1-2 文で説明]

## 変更内容

- [主要な変更点 1]
- [主要な変更点 2]
- [主要な変更点 3]

## テスト方法

```bash
[動作確認手順]
```

## チェックリスト

- [ ] テスト追加
- [ ] 型チェック通過
- [ ] Lint通過
- [ ] ドキュメント更新
- [ ] セキュリティチェック（API キー、秘密鍵の露出なし）

Closes #XX
```

### 4. マージ

#### マージ戦略：Squash and Merge 推奨

**メリット**:
- **綺麗な履歴**: main ブランチに 1 PR = 1 コミットとして記録される
- **読みやすさ**: WIP コミットや修正コミットが main に残らない

#### マージ後の作業

```bash
# ローカルブランチを削除
git checkout main
git pull origin main
git branch -d feature/2-websocket-connection
```

---

## コーディング規約

### Python

#### 1. 型ヒント必須

```python
# GOOD: 型ヒントあり
def calculate_distance_bps(order_price: float, mark_price: float) -> float:
    return abs(order_price - mark_price) / mark_price * 10000

# BAD: 型ヒントなし
def calculate_distance_bps(order_price, mark_price):
    return abs(order_price - mark_price) / mark_price * 10000
```

#### 2. 早期リターン

```python
# GOOD: 早期リターン
def process_order(order: Order | None) -> bool:
    if order is None:
        return False
    if not order.is_valid():
        return False

    return order.submit()

# BAD: ネストが深い
def process_order(order: Order | None) -> bool:
    if order is not None:
        if order.is_valid():
            return order.submit()
    return False
```

#### 3. async/await 一貫性

```python
# GOOD: async関数内ではawaitを使用
async def fetch_price(symbol: str) -> float:
    response = await client.get(f"/api/query_symbol_price?symbol={symbol}")
    return response["mark_price"]

# BAD: asyncとsyncの混在
async def fetch_price(symbol: str) -> float:
    response = requests.get(...)  # 同期呼び出し
    return response.json()["mark_price"]
```

#### 4. Ruff / Black 準拠

```bash
# フォーマット
ruff format .

# Lint
ruff check .

# 型チェック
mypy .
```

### 設定ファイル

#### 1. 秘密情報は環境変数

```python
# GOOD: 環境変数から取得
import os

PRIVATE_KEY = os.environ["STANDX_PRIVATE_KEY"]
WALLET_ADDRESS = os.environ["STANDX_WALLET_ADDRESS"]

# BAD: ハードコード
PRIVATE_KEY = "0x1234..."  # 絶対NG
```

#### 2. .env は .gitignore に追加

```gitignore
# .gitignore
.env
.env.local
*.pem
*_key.json
```

---

## テスト方針

### pytest 必須

すべての新機能・修正にはテストを追加してください。

#### ユニットテスト

```python
# tests/test_order.py
import pytest
from standx_mm_bot.order import calculate_distance_bps

def test_calculate_distance_bps():
    """mark_priceからの距離をbpsで計算"""
    mark_price = 3000.0
    order_price = 2997.0

    result = calculate_distance_bps(order_price, mark_price)

    assert result == 10.0  # 10 bps
```

#### 非同期テスト

```python
# tests/test_websocket.py
import pytest

@pytest.mark.asyncio
async def test_websocket_connection():
    """WebSocket接続が成功すること"""
    client = WebSocketClient(url="wss://...")

    await client.connect()

    assert client.is_connected
    await client.disconnect()
```

### テスト実行

```bash
# 全テスト実行
pytest

# 特定ファイルのみ
pytest tests/test_order.py

# カバレッジ付き
pytest --cov=standx_mm_bot
```

---

## コードレビュー基準

### 必須チェック項目

- [ ] **機能要件**: Issue の要件を満たしているか
- [ ] **テスト**: 十分なテストが追加されているか
- [ ] **型チェック**: mypy が通るか
- [ ] **Lint**: ruff check が通るか
- [ ] **命名**: 変数、関数、クラス名が適切か
- [ ] **エラーハンドリング**: 適切な例外処理があるか
- [ ] **セキュリティ**: 秘密情報の露出がないか

### セキュリティチェック

#### 1. 秘密鍵・APIキーの管理

**DO**: 環境変数から取得

```python
import os
PRIVATE_KEY = os.environ["STANDX_PRIVATE_KEY"]
```

**DON'T**: コードにハードコード、ログ出力

```python
PRIVATE_KEY = "0x1234..."  # NG
logger.info(f"Key: {PRIVATE_KEY}")  # NG
```

#### 2. .env ファイルのコミット防止

```bash
# コミット前に確認
git status
# .env が含まれていないこと
```

#### 3. ログ出力の注意

```python
# GOOD: 秘密情報をマスク
logger.info(f"Wallet: {address[:6]}...{address[-4:]}")

# BAD: 秘密情報をそのまま出力
logger.info(f"Private key: {private_key}")
```

### リスク制御チェック

Bot 特有のチェック項目：

- [ ] **ポジション上限**: net position の上限チェックがあるか
- [ ] **エラー時の挙動**: API エラー時に注文が残り続けないか
- [ ] **再接続ロジック**: WebSocket 切断時に適切に再接続するか
- [ ] **空白時間**: 注文の再配置時に板から消える時間が最小化されているか

---

## 参考リンク

- [StandX API Docs](https://docs.standx.com/standx-api/standx-api)
- [GitHub Flow](https://docs.github.com/ja/get-started/quickstart/github-flow)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Ruff](https://docs.astral.sh/ruff/)
- [pytest](https://docs.pytest.org/)

---

## 質問・サポート

- **Issue**: GitHub Issues で質問・報告
