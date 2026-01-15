# CLAUDE.md

Claude 向けクイックリファレンス。

---

## ドキュメント役割分担

| ドキュメント        | 役割                                                   |
| ------------------- | ------------------------------------------------------ |
| **README.md**       | プロジェクト概要、技術スタック、クイックスタート、トラブルシューティング |
| **CONTRIBUTING.md** | 開発規約（Issue、Git、コミット、PR、コーディング規約） |
| **CLAUDE.md**       | AI 向けクイックリファレンス（このファイル）            |

**詳細な開発規約は [CONTRIBUTING.md](./CONTRIBUTING.md) を参照。**

---

## プロジェクト概要

**StandX MM Bot** - StandX の Maker Points / Maker Uptime を最大化する Market Making Bot

### 目的

**約定させずに板に居続けること**を自動化する。

```
約定 = 失敗
```

| 項目 | 方針 |
|------|------|
| 約定 | **しない**（手数料ゼロ、FRリスクゼロ） |
| 建玉 | **持たない**（清算リスクゼロ） |
| 距離 | 10bps以内だが約定しない位置 |

### 報酬条件

| 報酬 | 条件 | Bot の役割 |
|------|------|-----------|
| Maker Points | mark_price ± 10bps 以内、3秒以上 | 距離維持 |
| Maker Uptime | 両サイド ± 10bps、毎時30分以上 | 空白時間ゼロ |

### 技術スタック

- **Python 3.12+** / asyncio / aiohttp / websockets
- **pydantic-settings** (設定管理)
- **Ruff** (Lint/Format) / **mypy** (型チェック) / **pytest** (テスト)

---

## ディレクトリ構成

```
standx_mm_bot/
├── src/standx_mm_bot/
│   ├── __main__.py        # エントリーポイント
│   ├── config.py          # 設定管理
│   ├── auth.py            # JWT認証
│   ├── client/
│   │   ├── http.py        # REST API
│   │   └── websocket.py   # WebSocket
│   ├── core/
│   │   ├── order.py       # 注文管理
│   │   └── escape.py      # 約定回避ロジック
│   └── strategy/
│       └── maker.py       # Maker戦略
├── tests/
├── pyproject.toml
└── Makefile
```

---

## よく使うコマンド

```bash
# 起動
make run

# テスト
make test

# 型チェック + Lint + テスト
make check

# フォーマット
make format
```

---

## コミット規約

```bash
# フォーマット
<type>(<scope>): <subject> (issue#XX)

# 例
feat(ws): WebSocket接続を実装 (issue#2)
fix(escape): 約定回避ロジックを修正 (issue#3)
```

**Scope**: `auth`, `ws`, `order`, `escape`, `config`, `docs`

**禁止事項**:
- main ブランチへの直接プッシュ
- issue 番号なしのコミット

---

## 開発ワークフロー

```bash
# 1. ブランチ作成
git checkout main && git pull
git checkout -b feature/XX-description

# 2. 実装・テスト

# 3. コミット
git add .
git commit -m "feat(scope): 内容 (issue#XX)"

# 4. PR作成
gh pr create --title "タイトル" --body "Closes #XX"
```

---

## セキュリティ注意事項

```python
# DO: 環境変数から取得
import os
PRIVATE_KEY = os.environ["STANDX_PRIVATE_KEY"]

# DON'T: ハードコード
PRIVATE_KEY = "0x1234..."  # NG

# DON'T: ログ出力
logger.info(f"Key: {private_key}")  # NG
```

- `.env` は絶対にコミットしない
- 秘密鍵、APIキーはログに出力しない

---

## API クイックリファレンス

### Base URL

```
REST: https://perps.standx.com
WS: wss://perps.standx.com/ws-stream/v1
```

### 主要エンドポイント

| 用途 | パス |
|------|------|
| 価格取得 | `GET /api/query_symbol_price?symbol=ETH_USDC` |
| 注文発注 | `POST /api/new_order` |
| 注文キャンセル | `POST /api/cancel_order` |
| 未決注文 | `GET /api/query_open_orders` |

### WebSocket チャンネル

| チャンネル | 認証 | 用途 |
|-----------|------|------|
| `price` | 不要 | mark_price |
| `order` | 必要 | 注文状態 |
| `depth_book` | 不要 | 板情報（約定回避判断用） |

---

## Bot ロジック要点

### 設計思想

```
価格が近づいてきたら → 逃げる
価格が離れたら → 戻る
```

### bps 計算

```python
distance_bps = abs(order_price - mark_price) / mark_price * 10000
```

### 約定回避ロジック

```python
# 価格が注文に近づいたら逃げる
if distance_to_order < ESCAPE_THRESHOLD_BPS:  # 3bps
    cancel_order() or move_to_outer(15bps)

# 価格が離れたら戻る
if distance_to_order > RETURN_THRESHOLD_BPS:
    move_to_target(8bps)
```

### 優先順位

1. **約定回避** — 最優先。建玉を持たない
2. **10bps維持** — Uptime条件を満たす
3. **空白時間最小化** — 板に常に存在

### 空白時間最小化

```
1. 新価格で新規注文発注
2. 確認後、旧注文キャンセル
```

キャンセル→発注ではなく、発注→キャンセルの順序。

---

## 関連リンク

- [README.md](./README.md)
- [CONTRIBUTING.md](./CONTRIBUTING.md)
- [StandX API Docs](https://docs.standx.com/standx-api/standx-api)
