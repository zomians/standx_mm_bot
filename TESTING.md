# テスト・運用ガイド

StandX MM Bot の安全なテスト手順と運用ガイド。

**⚠️ 重要**: 本番環境で起動する前に、必ずこのガイドに従ってテストを実施してください。

---

## 目次

- [概要](#概要)
- [前提条件](#前提条件)
- [Phase 1: 環境準備](#phase-1-環境準備)
- [Phase 2: 本番起動（段階的）](#phase-2-本番起動段階的)
- [Phase 3: 監視・運用](#phase-3-監視運用)
- [トラブルシューティング](#トラブルシューティング)
- [FAQ](#faq)

---

## 概要

このガイドでは、StandX MM Botを安全にテスト・運用するための手順を説明します。

### 段階的アプローチ

**最初は小さく、安定したら増やす**

```
ステップ1: ORDER_SIZE=0.001で開始（リスク ~$7）
    ↓ 1時間動作確認
ステップ2: ORDER_SIZE=0.01に増やす（リスク ~$70）
    ↓ 1日動作確認
ステップ3: さらに増やす（オプション）
```

### テストフロー全体図

```
Phase 1: 環境準備
├─ DUSD入金
├─ 残高確認
└─ 設定ファイル確認
    ↓
Phase 2: 本番起動（段階的）
├─ 2.1 初回起動（ORDER_SIZE=0.001）
├─ 2.2 動作確認（1時間）
├─ 2.3 ORDER_SIZE増加（0.01）
└─ 2.4 安定稼働
    ↓
Phase 3: 監視・運用
├─ ログ監視
├─ 異常検知
└─ 定期メンテナンス
```

---

## 前提条件

### 必須項目

以下が完了していることを確認してください：

- [ ] Docker / Docker Compose インストール済み
- [ ] リポジトリクローン済み
- [ ] `.env` ファイル設定済み
- [ ] BSC Wallet に BNB（ガス代）あり
- [ ] StandX Exchange に DUSD 入金済み

### 推奨環境

| 項目 | ORDER_SIZE=0.001 | ORDER_SIZE=0.01 | ORDER_SIZE=0.1 |
|------|------------------|-----------------|----------------|
| **必要額（両サイド）** | ~$7 | ~$70 | ~$700 |
| **推奨残高** | $10以上 | $100以上 | $1,000以上 |
| **BNB残高** | 0.005 BNB (~$3) | 0.005 BNB (~$3) | 0.01 BNB (~$6) |

**⚠️ 重要**: ORDER_SIZE × ETH価格 × 2（両サイド）の残高が必要です。

**例（ETH価格 $3,500の場合）:**
- ORDER_SIZE=0.001 → 必要額: ~$7
- ORDER_SIZE=0.01 → 必要額: ~$70
- ORDER_SIZE=0.1 → 必要額: ~$700

### 確認コマンド

```bash
# Docker確認
docker --version
docker compose version

# 残高確認
make balance

# 設定確認
make config
```

---

## Phase 1: 環境準備

### 1.1 DUSD入金

**⚠️ この手順は1回だけ実施**

#### ステップ1: DUSDミント

1. https://standx.com にアクセス
2. ウォレット接続（BSC Network）
3. Mintタブで USDT/USDC → DUSD
4. 金額入力（推奨: 10 DUSD以上）
5. トランザクション承認
6. 完了待機（1-3分）

**コスト:**
- ミント手数料: 無料（1:1レート）
- ガス代: ~$0.20

#### ステップ2: StandX入金

1. StandXサイトで "Deposit" / "Transfer to Perps Wallet"
2. DUSD金額を入力
3. トランザクション承認
4. 完了確認

**コスト:**
- ガス代: ~$0.20

#### ステップ3: 残高確認

```bash
make balance
```

**期待される出力:**

```
💰 StandX Exchange Balance
╭─────────────────────────────┬────────╮
│ Field                       │  Value │
├─────────────────────────────┼────────┤
│ Equity (資産額)             │ $10.00 │  ← DUSD入金成功
│ Available (利用可能額)      │ $10.00 │
│ Locked (ロック額)           │  $0.00 │
│ Unrealized PnL (未実現損益) │ +$0.00 │
╰─────────────────────────────┴────────╯

🔗 BSC Wallet Balance
╭───────┬─────────╮
│ Token │ Balance │
├───────┼─────────┤
│ BNB   │  0.0040 │  ← ガス代残っている
│ USDC  │   $0.00 │
│ USDT  │   $0.00 │
╰───────┴─────────╯
```

**チェックリスト:**

- [ ] StandX Equity が 10 DUSD以上
- [ ] BNB 残高が 0.003 BNB以上
- [ ] Locked が 0（建玉なし）

### 1.2 設定ファイル確認

```bash
make config
```

**重要な設定項目:**

```env
STANDX_CHAIN=bsc              # BSC使用
SYMBOL=ETH-USD                # 取引ペア
ORDER_SIZE=0.001              # ⚠️ 最初は0.001で開始
TARGET_DISTANCE_BPS=8.0       # 目標距離 8bps
ESCAPE_THRESHOLD_BPS=3.0      # 逃げる距離 3bps
```

**設定変更方法:**

```bash
# .envファイルを編集
vim .env

# または
nano .env
```

**チェックリスト:**

- [ ] `ORDER_SIZE=0.001` に設定（最初は最小値）
- [ ] `SYMBOL` が意図した取引ペア
- [ ] ウォレットアドレスが正しい

---

## Phase 2: 本番起動（段階的）

### 2.1 初回起動（ORDER_SIZE=0.001）

**リスク最小（~$7）で実際の動作を確認**

#### Bot起動

```bash
# Bot起動
make up

# ログ監視（必須！）
make logs -f
```

#### 起動直後の確認

```
[INFO] Starting StandX MM Bot
[INFO] Chain: bsc
[INFO] Symbol: ETH-USD
[INFO] Order size: 0.001  ← 最小値確認
[INFO] WebSocket connected
[INFO] Placing initial orders...
[INFO] Buy order placed: order_id=xxx, price=3472.00, size=0.001
[INFO] Sell order placed: order_id=xxx, price=3528.00, size=0.001
```

**チェックリスト:**

- [ ] `Order size: 0.001` 表示
- [ ] 両サイド注文が発注された
- [ ] order_id が返ってきた
- [ ] エラーがない

#### 注文状態の確認

**別ターミナルで確認:**

```bash
docker compose run --rm bot python scripts/read_api.py status
```

**期待される出力:**

```
📊 Open Orders
╭──────────┬──────┬────────┬───────┬────────╮
│ Order ID │ Side │  Price │  Size │ Status │
├──────────┼──────┼────────┼───────┼────────┤
│ xxx      │ BUY  │ 3472.0 │ 0.001 │ OPEN   │
│ yyy      │ SELL │ 3528.0 │ 0.001 │ OPEN   │
╰──────────┴──────┴────────┴───────┴────────╯

📈 Position
╭──────────┬──────────╮
│ Position │      0.0 │  ← ゼロであること
╰──────────┴──────────╯
```

**チェックリスト:**

- [ ] 両サイド（BUY/SELL）の注文が存在
- [ ] Size が 0.001
- [ ] Status が OPEN
- [ ] Position が 0

### 2.2 動作確認（1時間監視）

**最低1時間は動作を監視してください。**

#### ログで確認すべき項目

1. **価格更新**
   ```
   [INFO] Price update: ETH-USD mark_price=3500.00
   ```

2. **距離維持**
   ```
   [INFO] Buy order distance: 8.0 bps
   [INFO] Sell order distance: 8.0 bps
   ```

3. **約定回避動作**（価格が動いた場合）
   ```
   [INFO] Price approaching buy order: distance=2.5 bps
   [INFO] Cancelling buy order: order_id=xxx
   [INFO] Placing new buy order: price=3447.50 (15 bps)
   ```

**チェックリスト:**

- [ ] 1時間エラーなく動作
- [ ] 価格が定期的に更新される
- [ ] 距離が10bps以内に維持される
- [ ] 価格変動時に適切に再配置される
- [ ] Position が常に 0
- [ ] 約定しなかった

#### ⚠️ 異常検知

**即座に停止すべき状況:**

1. **約定した**
   ```
   [INFO] Order filled: order_id=xxx
   [INFO] Position: 0.001  ← ゼロでない！
   ```
   → 即座に `make down` で停止
   → StandX UIで成行クローズ

2. **エラー頻発**
   ```
   [ERROR] Order placement failed
   [ERROR] API request failed
   ```
   → 停止して原因調査

3. **残高異常**
   ```
   Available: -$1.00  ← マイナス！
   ```
   → 即座に停止

### 2.3 ORDER_SIZE増加（0.01）

**1時間正常動作したら、ORDER_SIZEを増やす:**

#### ステップ1: Bot停止

```bash
make down
```

#### ステップ2: ORDER_SIZE変更

`.env` ファイルを編集:

```bash
vim .env
```

**変更箇所:**

```diff
- ORDER_SIZE=0.001
+ ORDER_SIZE=0.01  # 10倍
```

#### ステップ3: 残高確認

**必要額（ETH価格$3,500想定）:**
- ORDER_SIZE: 0.01 ETH
- 片側: 0.01 × $3,500 = $35
- 両サイド: $35 × 2 = **$70**
- 推奨残高: **$100以上**

```bash
make balance
```

**チェックリスト:**

- [ ] StandX Equity が $100以上
- [ ] Available が $70以上
- [ ] Position が 0

#### ステップ4: 再起動

```bash
# Bot再起動
make up

# ログ監視
make logs -f
```

**確認:**

```
[INFO] Order size: 0.01  ← 増加確認
[INFO] Buy order placed: size=0.01
[INFO] Sell order placed: size=0.01
```

### 2.4 安定稼働

**ORDER_SIZE=0.01で1日動作確認:**

- [ ] 24時間エラーなく動作
- [ ] 約定回数が少ない（週1回以下）
- [ ] Position = 0 を維持
- [ ] Maker Points/Uptimeが貯まっている

**さらに増やす（オプション）:**

安定稼働が確認できたら、ORDER_SIZEをさらに増やせます：
- 0.01 → 0.02
- 0.02 → 0.05
- 0.05 → 0.1

**ただし:**
- 必ず残高を確認
- 段階的に増やす
- 各段階で動作確認

---

## Phase 3: 監視・運用

### 3.1 ログ監視

#### リアルタイム監視

```bash
make logs -f
```

#### ログフィルタリング

```bash
# エラーのみ表示
make logs | grep ERROR

# 価格更新のみ
make logs | grep "mark_price"

# 注文関連のみ
make logs | grep "order"
```

### 3.2 定期チェック項目

#### 1時間ごと

- [ ] Botが稼働中（`docker ps`）
- [ ] エラーログがない
- [ ] Position = 0

```bash
# 稼働確認
docker ps | grep standx_mm_bot

# Position確認
docker compose run --rm bot python scripts/read_api.py status | grep Position
```

#### 1日ごと

- [ ] 残高確認（DUSD減っていないか）
- [ ] ガス代残高（BNB）
- [ ] 異常なトレード履歴がないか

```bash
# 残高確認
make balance

# トレード履歴確認（StandX UI）
```

#### 1週間ごと

- [ ] Logファイルサイズ確認
- [ ] Docker再起動（任意）
- [ ] アップデート確認

```bash
# ログサイズ確認
docker compose logs --tail=100 bot | wc -l

# 再起動（任意）
make down && make up
```

### 3.3 Maker Points確認

StandX UIで確認:

- Maker Points: 10bps以内、3秒以上で加算
- Maker Uptime: 両サイド10bps以内、30分以上で加算

**確認方法:**

1. https://standx.com にアクセス
2. Pointsページで確認

### 3.4 緊急停止方法

**何か問題があれば即座に停止:**

```bash
# Bot停止
make down

# または実行中のターミナルで
Ctrl + C
```

**停止後の確認:**

```bash
# 注文状態確認
docker compose run --rm bot python scripts/read_api.py status

# 建玉があればクローズ（手動）
# StandX UIで成行クローズ
```

---

## トラブルシューティング

### よくある問題と解決方法

#### 問題1: Botが起動しない

**エラー:**
```
Error: No such file or directory: .env
```

**原因:**
`.env` ファイルが存在しない

**解決方法:**
```bash
cp .env.example .env
vim .env  # 設定を編集
```

---

#### 問題2: WebSocket接続失敗

**エラー:**
```
[ERROR] WebSocket connection failed
```

**原因:**
- ネットワークエラー
- StandX APIダウン

**解決方法:**
```bash
# ネットワーク確認
ping perps.standx.com

# 再起動
make down && make up
```

---

#### 問題3: 注文発注失敗

**エラー:**
```
[ERROR] Order placement failed: Insufficient balance
```

**原因:**
DUSD残高不足

**解決方法:**
```bash
# 残高確認
make balance

# DUSD追加入金
# または ORDER_SIZE を小さくする
```

---

#### 問題4: 約定した

**ログ:**
```
[INFO] Order filled: order_id=xxx, side=BUY
[INFO] Position: 0.001
```

**対処:**
1. 即座に `make down` で停止
2. StandX UIで成行クローズ
3. パラメータ見直し

**パラメータ調整例:**
```env
# より早く逃げる
ESCAPE_THRESHOLD_BPS=5.0  # 3.0 → 5.0

# より遠くに逃げる
OUTER_ESCAPE_DISTANCE_BPS=20.0  # 15.0 → 20.0
```

---

#### 問題5: ガス代不足

**エラー:**
```
[ERROR] Transaction failed: insufficient funds for gas
```

**原因:**
BNB残高不足

**解決方法:**
```bash
# BNB残高確認
make balance

# BNB追加送金（0.005 BNB推奨）
```

---

## FAQ

### Q1: 最初はどのくらいのORDER_SIZEで始めるべきですか？

**A:** 必ず **ORDER_SIZE=0.001** から開始してください。

理由：
- リスク最小（~$7のロック）
- 実際のAPIを検証できる
- 約定しても損失は数セント

### Q2: ORDER_SIZEはどのくらいまで増やせますか？

**A:** 残高に応じて段階的に：

| 残高 | 推奨ORDER_SIZE |
|------|---------------|
| $10-50 | 0.001 |
| $100-500 | 0.01-0.02 |
| $1,000以上 | 0.05-0.1 |

**重要:** ORDER_SIZE × 価格 × 2 の残高が必要

### Q3: 約定した場合、どうすればいいですか？

**A:** 以下の手順で対応：

1. `make down` で即停止
2. StandX UIで成行クローズ（建玉ゼロに）
3. パラメータ見直し
4. ORDER_SIZE=0.001で再テスト

### Q4: ガス代（BNB）はどのくらい必要ですか？

**A:** 以下を目安に：

- **1日運用**: 0.001 BNB (~$0.60)
- **1週間運用**: 0.005 BNB (~$3.00)
- **1ヶ月運用**: 0.02 BNB (~$12.00)

### Q5: Botを長期間稼働させても大丈夫ですか？

**A:** 以下を守れば問題ありません：

- 定期的な監視（1日1回以上）
- ログ確認
- 残高チェック
- 定期再起動（1週間に1回推奨）

### Q6: 複数のシンボル（ETH-USD、BTC-USD）を同時に運用できますか？

**A:** 可能ですが、推奨しません：

- 各シンボルごとに別のインスタンス起動が必要
- 残高管理が複雑になる
- まずは1シンボルで安定稼働させることを推奨

---

## まとめ

### 安全なテストの流れ

```
✅ Phase 1: 環境準備
  → DUSD入金、設定確認

✅ Phase 2: 本番起動（段階的）
  ├─ ORDER_SIZE=0.001で開始（リスク最小）
  ├─ 1時間動作確認
  ├─ ORDER_SIZE=0.01に増やす
  └─ 安定稼働

✅ Phase 3: 監視・運用
  → 定期チェック、異常検知
```

### 重要な原則

1. **最初は小さく始める**（ORDER_SIZE=0.001）
2. **段階的に増やす**（0.001 → 0.01 → 0.05）
3. **定期的な監視**
4. **異常時は即停止**

### 次のステップ

- Phase 1から順番に実施
- 各Phaseのチェックリスト完了を確認
- 問題があれば[トラブルシューティング](#トラブルシューティング)参照

---

**関連ドキュメント:**

- [README.md](./README.md) - プロジェクト概要
- [CONTRIBUTING.md](./CONTRIBUTING.md) - 開発ガイド
- [GUIDE.md](./GUIDE.md) - 技術解説
- [DESIGN.md](./DESIGN.md) - 設計詳細

---

**Last Updated**: 2026-01-22
