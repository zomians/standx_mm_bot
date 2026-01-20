# 開発ガイド

StandX MM Bot プロジェクトへようこそ！このガイドでは、プロジェクトへの貢献方法と開発ワークフローを説明します。

---

## ドキュメント役割分担

各ドキュメントの役割を明確に分離し、情報の重複を避けています。

| コンテンツ               | README.md | CONTRIBUTING.md | CLAUDE.md | GUIDE.md | DESIGN.md |
| ------------------------ | :-------: | :-------------: | :-------: | :------: | :-------: |
| **プロジェクト概要**     |     ◎     |        −        |     ○     |    ○     |     ○     |
| **技術スタック**         |     ◎     |        −        |     ○     |    ◎     |     ○     |
| **クイックスタート**     |     ◎     |        −        |     ○     |    −     |     −     |
| **ディレクトリ構成**     |     ◎     |        −        |     ○     |    ○     |     ◎     |
| **よく使うコマンド**     |     ◎     |        −        |     ◎     |    −     |     −     |
| **トラブルシューティング** |     ◎     |        −        |     ○     |    ◎     |     −     |
| **ドキュメント役割分担** |     −     |        ◎        |     ○     |    ○     |     −     |
| **Issue 作成ガイド**     |     −     |        ◎        |     ○     |    −     |     −     |
| **Git ワークフロー**     |     −     |        ◎        |     ○     |    −     |     −     |
| **コミット規約**         |     −     |        ◎        |     ○     |    −     |     −     |
| **PR 作成フロー**        |     −     |        ◎        |     ○     |    −     |     −     |
| **コーディング規約**     |     −     |        ◎        |     −     |    −     |     −     |
| **テスト方針**           |     −     |        ◎        |     −     |    ○     |     ◎     |
| **コードレビュー基準**   |     −     |        ◎        |     −     |    −     |     −     |
| **セキュリティチェック** |     −     |        ◎        |     ○     |    ○     |     −     |
| **理論的背景**           |     −     |        −        |     −     |    ◎     |     −     |
| **技術基礎解説**         |     −     |        −        |     −     |    ◎     |     −     |
| **設計思想詳解**         |     −     |        −        |     ○     |    ◎     |     ○     |
| **数学的モデル**         |     −     |        −        |     −     |    ◎     |     ○     |
| **実装ガイド**           |     −     |        −        |     −     |    ◎     |     −     |
| **アーキテクチャ詳細**   |     −     |        −        |     −     |    ○     |     ◎     |
| **実装フェーズ**         |     −     |        −        |     −     |    −     |     ◎     |
| **判断ロジック**         |     −     |        −        |     ○     |    ◎     |     ◎     |
| **パラメータ設定**       |     ◎     |        −        |     −     |    ○     |     ◎     |
| **データモデル**         |     −     |        −        |     −     |    ○     |     ◎     |
| **API 仕様**             |     ◎     |        −        |     ○     |    ○     |     ◎     |
| **エラーハンドリング**   |     −     |        −        |     −     |    ○     |     ◎     |

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
## 📋 概要

[1-2文で変更内容を簡潔に説明]

**関連issue**: [関連するIssue番号があれば記載]

---

## 🎯 背景・課題

### 現状の問題
- [現在どのような問題があるか]
- [なぜこの変更が必要なのか]

### 課題
- ❌ [具体的な課題1]
- ❌ [具体的な課題2]
- ❌ [具体的な課題3]

---

## 🎯 目的・ゴール

### 主目的
[この変更で達成したいこと]

### 副次的目標
- [追加で達成したいこと1]
- [追加で達成したいこと2]

---

## 📖 要件定義

### 機能要件

#### FR-1: [機能名1]
- [詳細な要件説明]
- [実装内容]

#### FR-2: [機能名2]
- [詳細な要件説明]
- [実装内容]

### 非機能要件

#### NFR-1: パフォーマンス
- [パフォーマンス要件]

#### NFR-2: セキュリティ
- [セキュリティ要件]

#### NFR-3: 保守性
- [保守性要件]

---

## 🛠️ 技術仕様

### アーキテクチャ

[システム構成図、フロー図など]

### 実装詳細

[具体的な実装方法、コード例など]

---

## ✅ 受け入れ基準

### 必須（Must Have）
- [ ] [必須要件1]
- [ ] [必須要件2]

### 推奨（Should Have）
- [ ] [推奨要件1]
- [ ] [推奨要件2]

### オプション（Nice to Have）
- [ ] [オプション要件1]
- [ ] [オプション要件2]

---

## ⏱️ 工数見積

### タスク分解

| タスク | 内容 | 見積工数 |
|--------|------|----------|
| **設計** | [設計内容] | X.Xh |
| **実装** | [実装内容] | X.Xh |
| **テスト** | [テスト内容] | X.Xh |
| **ドキュメント更新** | [ドキュメント更新内容] | X.Xh |

**合計見積: X時間（X営業日）**
**バッファ（+25%）: X時間**

---

## 🧪 テスト計画

### テストケース

#### TC-1: [テストケース名1]
- **手順**:
  1. [手順1]
  2. [手順2]
- **期待結果**: [期待される結果]

#### TC-2: [テストケース名2]
- **手順**:
  1. [手順1]
  2. [手順2]
- **期待結果**: [期待される結果]

---

## 📈 次のステップ

[この機能完了後の展開、将来の拡張など]

---

## 📚 関連資料

- [関連ドキュメント、外部リンクなど]

---

## ✅ Definition of Done

- [ ] [完了条件1]
- [ ] [完了条件2]
- [ ] すべてのテストケース合格
- [ ] ドキュメント更新完了
- [ ] コードレビュー承認

---

**工数見積**: X時間（X営業日）
**優先度**: High/Medium/Low
**難易度**: High/Medium/Low
**依存関係**: [依存するIssueや前提条件]
```

### 優先度と難易度の定義

#### 優先度（Priority）

| レベル | 説明 | 例 |
|--------|------|-----|
| **High** | 本番運用に必須、ブロッカー | セキュリティ修正、重大なバグ修正 |
| **Medium** | 重要だが緊急ではない | 新機能、パフォーマンス改善 |
| **Low** | あると良い、将来的に対応 | リファクタリング、ドキュメント追加 |

#### 難易度（Difficulty）

| レベル | 説明 | 見積工数目安 |
|--------|------|-------------|
| **Low** | 単純な変更、影響範囲が小さい | 〜4時間 |
| **Medium** | 複数ファイルの変更、設計が必要 | 4〜16時間 |
| **High** | アーキテクチャ変更、複数モジュール横断 | 16時間〜 |

---

## 工数見積ガイドライン

### タスク分解の基本

すべての Issue は以下の標準タスクに分解してください：

| タスク | 内容 | 一般的な割合 |
|--------|------|------------|
| **設計** | 技術仕様の詳細化、アーキテクチャ検討 | 15-20% |
| **実装** | コーディング、リファクタリング | 40-50% |
| **テスト** | テストコード作成、動作確認 | 20-25% |
| **ドキュメント更新** | README、ドキュメント更新 | 10-15% |

### 見積単位

- **時間単位**: 0.5時間刻みで見積もる
- **営業日換算**: 1営業日 = 8時間
- **最小単位**: 0.5時間
- **最大単位**: 1つのIssueは16時間（2営業日）を超えないように分割

### 確実性レベルとバッファ

| レベル | 説明 | バッファ |
|--------|------|---------|
| **高確実性** | 過去に類似実装あり、技術スタック熟知 | +10% |
| **中確実性** | 一般的な実装パターン、ドキュメント充実 | +25% |
| **低確実性** | 初めての技術、調査が必要 | +50% |

### 見積例

**例1: 簡単な機能追加（Low難易度）**

```
設計: 0.5h
実装: 1.5h
テスト: 0.5h
ドキュメント: 0.5h
---
合計: 3h（0.375営業日）
バッファ（+25%）: 3.75h → 切り上げて 4h
```

**例2: 複雑なロジック実装（Medium難易度）**

```
設計: 1.0h
実装: 4.0h
テスト: 2.0h
ドキュメント: 1.0h
---
合計: 8h（1営業日）
バッファ（+25%）: 10h → 切り上げて 10h
```

### 見積時の注意事項

1. **楽観的すぎない**: 最速ケースではなく、現実的な時間を見積もる
2. **テスト時間を忘れない**: 実装時間の50-60%をテストに割く
3. **ドキュメント更新を含める**: 後回しにしがちだが必須
4. **依存関係を考慮**: 他のタスクをブロックする場合は優先度を上げる
5. **レビュー時間は含めない**: レビューアの時間は別途

### バッファの考え方

- **予期しない問題**: 環境構築エラー、依存関係の競合など
- **仕様の曖昧性**: 実装中に発覚する仕様の不明点
- **テスト失敗対応**: バグ修正、リファクタリング

**推奨**: 常に+25%のバッファを含め、0.5時間単位で切り上げ

---

## Git ワークフロー

このプロジェクトは **[GitHub Flow](https://docs.github.com/ja/get-started/quickstart/github-flow)** を採用しています。

### 🚨 重要な原則：ブランチを作ってから作業する

**作業を開始する前に、必ず以下の手順を守ってください：**

1. **❌ main ブランチで直接作業しない**
   ```bash
   # ❌ BAD: main ブランチで直接編集
   git checkout main
   vim some_file.py  # 危険！
   ```

2. **✅ Issue 作成 → ブランチ作成 → 実装の順序を守る**
   ```bash
   # ✅ GOOD: 正しい手順
   # Step 1: Issue 作成（GitHub で実施）
   # Step 2: main を最新化 👈 これを忘れない！
   git checkout main
   git pull origin main  # 🚨 必須！古いコードから分岐するとコンフリクト多発

   # Step 3: 新しいブランチを作成
   git checkout -b feature/12-websocket-connection

   # Step 4: 実装開始
   vim some_file.py
   ```

3. **⚠️ 作業中にブランチが間違っていることに気づいた場合**
   ```bash
   # 変更を一時保存
   git stash

   # 正しいブランチに移動（または作成）
   git checkout main
   git pull origin main
   git checkout -b feature/XX-correct-branch

   # 変更を適用
   git stash pop
   ```

**なぜこれが重要か？**

- **main ブランチの保護**: main は常に安定した状態を保つ必要があります
- **変更の追跡**: 各機能・修正が独立したブランチで管理され、レビューが容易
- **ロールバック**: 問題があった場合、ブランチごと削除すれば main は影響を受けない
- **並行作業**: 複数の機能を同時進行できる

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
5. **ツール署名削除**: Claude Code の `🤖 Generated with Claude Code` 署名は削除してからコミット

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

このプロジェクトでは **Squash and Merge** を推奨します。

**✅ 推奨：Squash and Merge**

```bash
# GitHub UIで PR をマージする際、"Squash and merge" を選択
```

**メリット**:
- **綺麗な履歴**: main ブランチに 1 PR = 1 コミットとして記録される
- **読みやすさ**: WIP コミットや修正コミットが main に残らない
- **Conventional Commits**: PR タイトルがコミットメッセージになる
- **Issue ベース開発**: 1 Issue = 1 PR = 1 コミット

**例**:

```
# PR内のコミット履歴（開発中）
- WIP: 初期実装
- fix: typo修正
- refactor: コードレビュー対応
- test: テスト追加

↓ Squash and Merge

# mainブランチのコミット履歴（綺麗）
- feat(ws): WebSocket接続を実装 (issue#2)
```

**他のマージ戦略を使う場合**:

| 戦略 | 使用ケース | 例 |
|------|----------|-----|
| **Merge commit** | 複数の独立した機能を含む大きなPR | リリースブランチのマージ |
| **Rebase and merge** | コミット履歴を保持したい場合 | 詳細な変更履歴が重要な場合 |

**デフォルト**: Squash and Merge

#### マージ後の作業

```bash
# ローカルブランチを削除
git checkout main
git pull origin main
git branch -d feature/2-websocket-connection

# リモートブランチは GitHub が自動削除（設定により）
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
