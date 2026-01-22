# テスト・運用ガイド

StandX MM Bot の安全なテスト手順と運用ガイド。

**⚠️ 重要**: 本番環境で起動する前に、必ずこのガイドに従ってテストを実施してください。

---

## 目次

- [概要](#概要)
- [前提条件](#前提条件)
- [Phase 1: 環境準備](#phase-1-環境準備)
- [Phase 2: DRY_RUNテスト](#phase-2-dry_runテスト)
- [Phase 3: 本番起動](#phase-3-本番起動)
- [Phase 4: 監視・運用](#phase-4-監視運用)
- [トラブルシューティング](#トラブルシューティング)
- [FAQ](#faq)

---

## 概要

このガイドでは、StandX MM Botを安全にテスト・運用するための手順を説明します。

### テストの重要性

**なぜDRY_RUNテストが必要か:**

- ❌ 設定ミスによる想定外の注文
- ❌ 資金不足による注文失敗
- ❌ API接続エラーによる動作不良
- ❌ 約定回避ロジックの未検証

**DRY_RUNモードなら:**

- ✅ 実際の注文は発注されない
- ✅ ログでロジックを確認できる
- ✅ 設定ミスを事前に発見できる
- ✅ リスクゼロで動作確認できる

### テストフロー全体図

```
Phase 1: 環境準備
├─ DUSD入金
├─ 残高確認
└─ 設定ファイル確認
    ↓
Phase 2: DRY_RUNテスト
├─ DRY_RUN=True設定
├─ Bot起動・動作確認
└─ ログ分析
    ↓
Phase 3: 本番起動
├─ 最終チェック
├─ DRY_RUN=False設定
└─ 本番起動
    ↓
Phase 4: 監視・運用
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

| 項目 | 推奨値 |
|------|--------|
| BNB残高 | 0.005 BNB以上（~$3） |
| DUSD残高 | 10 DUSD以上 |
| ORDER_SIZE | 0.1-1.0（最小注文額以上） |

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
ORDER_SIZE=0.1                # 注文サイズ（DUSDベース）
TARGET_DISTANCE_BPS=8.0       # 目標距離 8bps
ESCAPE_THRESHOLD_BPS=3.0      # 逃げる距離 3bps
DRY_RUN=True                  # ⚠️ 必ずTrueで開始
```

**設定変更方法:**

```bash
# .envファイルを編集
vim .env

# または
nano .env
```

**チェックリスト:**

- [ ] `DRY_RUN=True` に設定
- [ ] `ORDER_SIZE` が最小注文額以上
- [ ] `SYMBOL` が意図した取引ペア
- [ ] ウォレットアドレスが正しい

---

## Phase 2: DRY_RUNテスト

### 2.1 DRY_RUNモードとは

**DRY_RUN=True の動作:**

- ✅ WebSocket接続・価格取得: **実行される**
- ✅ 注文計算・ロジック: **実行される**
- ❌ 実際の注文発注: **実行されない**
- ✅ ログ出力: **「DRY RUN」と表示**

**つまり:**

実際の注文は発注せずに、ロジックの動作だけを確認できます。

### 2.2 Bot起動

```bash
# Bot起動
make up

# ログ表示（別ターミナル）
make logs

# またはリアルタイム表示
make logs -f
```

### 2.3 ログ確認項目

#### ✅ 正常起動の確認

```
[INFO] Starting StandX MM Bot
[INFO] Chain: bsc
[INFO] Symbol: ETH-USD
[INFO] DRY RUN MODE: True  ← 重要！
[INFO] WebSocket connected
[INFO] Subscribed to price channel
[INFO] Subscribed to order channel
```

**チェックリスト:**

- [ ] `DRY RUN MODE: True` が表示される
- [ ] WebSocket接続成功
- [ ] チャンネル購読成功

#### ✅ 価格取得の確認

```
[INFO] Price update: ETH-USD mark_price=3500.00
```

**チェックリスト:**

- [ ] mark_price が定期的に更新される
- [ ] 価格が妥当な範囲（市場価格と一致）

#### ✅ 注文計算の確認

```
[INFO] Target prices calculated:
[INFO]   Buy:  3472.00 (8.0 bps below mark)
[INFO]   Sell: 3528.00 (8.0 bps above mark)
[DRY RUN] Would place buy order: price=3472.00, size=0.1
[DRY RUN] Would place sell order: price=3528.00, size=0.1
```

**チェックリスト:**

- [ ] Buy/Sell価格が計算されている
- [ ] 距離が `TARGET_DISTANCE_BPS` (8bps) になっている
- [ ] `[DRY RUN]` 表示がある（実注文なし）

#### ✅ 約定回避ロジックの確認

価格が注文に接近した場合:

```
[INFO] Price approaching buy order: distance=2.5 bps
[INFO] Escape threshold (3.0 bps) reached
[DRY RUN] Would cancel buy order: order_id=xxx
[DRY RUN] Would place new buy order: price=3447.50 (15.0 bps below)
```

**チェックリスト:**

- [ ] 接近検知が動作
- [ ] `ESCAPE_THRESHOLD_BPS` (3bps) で反応
- [ ] 逃げ先が `OUTER_ESCAPE_DISTANCE_BPS` (15bps)

### 2.4 動作確認チェックリスト

**Phase 2 完了基準:**

- [ ] Bot起動に成功（エラーなし）
- [ ] `DRY RUN MODE: True` 表示確認
- [ ] WebSocket接続・価格取得成功
- [ ] Buy/Sell注文計算が正しい
- [ ] 距離計算が正しい（8bps前後）
- [ ] 約定回避ロジックが動作
- [ ] エラーログがない

**⚠️ エラーがある場合:**

Phase 3 に進まず、[トラブルシューティング](#トラブルシューティング) を参照してください。

### 2.5 DRY_RUNテスト終了

```bash
# Bot停止
make down

# または Ctrl+C
```

---

## Phase 3: 本番起動

### ⚠️ 警告

**本番起動前の最終確認:**

- Phase 2 のDRY_RUNテストが完全に成功していること
- 全てのチェックリストが完了していること
- 残高が十分にあること

### 3.1 最終チェックリスト

**設定確認:**

- [ ] `DRY_RUN=True` で問題なく動作した
- [ ] 注文サイズが妥当（`ORDER_SIZE`）
- [ ] 残高が十分（注文サイズ × 2 + 余裕）
- [ ] 建玉がゼロ

**リスク理解:**

- [ ] 約定リスクを理解している
- [ ] 急激な価格変動時は約定する可能性がある
- [ ] 緊急停止方法を理解している

**残高確認:**

```bash
make balance
```

**期待される残高:**

```
Equity: $10以上
Available: ORDER_SIZE × 2 以上
Locked: $0
Position: 0
```

### 3.2 本番モード設定

`.env` ファイルを編集:

```bash
vim .env
```

**変更箇所:**

```diff
- DRY_RUN=True
+ DRY_RUN=False
```

**保存・確認:**

```bash
# 設定確認
make config | grep DRY_RUN
# → DRY_RUN=False が表示されること
```

### 3.3 本番起動

```bash
# Bot起動
make up

# ログ監視（必須！）
make logs -f
```

### 3.4 初期監視（最初の1時間）

#### ✅ 起動直後の確認

```
[INFO] Starting StandX MM Bot
[INFO] DRY RUN MODE: False  ← 本番モード確認
[INFO] WebSocket connected
[INFO] Placing initial orders...
[INFO] Buy order placed: order_id=xxx, price=3472.00
[INFO] Sell order placed: order_id=xxx, price=3528.00
```

**チェックリスト:**

- [ ] `DRY RUN MODE: False` 表示
- [ ] 初回注文が発注された
- [ ] order_id が返ってきた
- [ ] エラーがない

#### ✅ 注文状態の確認

```bash
# 別ターミナルで確認
docker compose run --rm bot python scripts/read_api.py status
```

**期待される出力:**

```
📊 Open Orders
╭──────────┬──────┬────────┬──────────┬────────╮
│ Order ID │ Side │  Price │     Size │ Status │
├──────────┼──────┼────────┼──────────┼────────┤
│ xxx      │ BUY  │ 3472.0 │      0.1 │ OPEN   │
│ yyy      │ SELL │ 3528.0 │      0.1 │ OPEN   │
╰──────────┴──────┴────────┴──────────┴────────╯

📈 Position
╭──────────┬──────────╮
│ Position │      0.0 │  ← ゼロであること
╰──────────┴──────────╯
```

**チェックリスト:**

- [ ] 両サイド（BUY/SELL）の注文が存在
- [ ] Status が OPEN
- [ ] Position が 0

#### ⚠️ 異常検知項目

**即座に停止すべき状況:**

1. **Position が 0 でない**
   ```
   Position: 0.5  ← 約定した！
   ```
   → 即座に `make down` で停止

2. **注文が片方しかない**
   ```
   Open Orders: 1件（BUYのみ）
   ```
   → 何らかのエラー、要調査

3. **距離が10bpsを超える**
   ```
   Buy: 3440.0 (17 bps below)
   ```
   → Maker Uptimeポイント対象外

4. **大量のエラーログ**
   ```
   [ERROR] API request failed
   [ERROR] Order placement failed
   ```
   → 即座に停止

### 3.5 緊急停止方法

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

## Phase 4: 監視・運用

### 4.1 ログ監視

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

### 4.2 定期チェック項目

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

### 4.3 Maker Points確認

StandX UIで確認:

- Maker Points: 10bps以内、3秒以上で加算
- Maker Uptime: 両サイド10bps以内、30分以上で加算

**確認方法:**

1. https://standx.com にアクセス
2. Pointsページで確認

### 4.4 パフォーマンス指標

#### 理想的な状態

- **Uptime**: 99%以上（空白時間ゼロ）
- **約定回数**: 0回（完全回避）
- **10bps維持率**: 100%

#### 許容範囲

- **Uptime**: 95%以上
- **約定回数**: 週1回以下（急変時のみ）
- **10bps維持率**: 98%以上

#### 問題状態

- **Uptime**: 90%未満 → 再配置ロジック要確認
- **約定回数**: 週2回以上 → パラメータ調整必要
- **10bps維持率**: 95%未満 → 距離計算要確認

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
[INFO] Position: 0.5
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

#### 問題6: 距離が10bpsを超える

**ログ:**
```
[INFO] Buy: 3440.0 (17 bps below mark)
```

**原因:**
- `TARGET_DISTANCE_BPS` 設定ミス
- 価格変動が大きすぎる

**解決方法:**
```bash
# 設定確認
make config | grep TARGET_DISTANCE_BPS

# .env修正
vim .env
# TARGET_DISTANCE_BPS=8.0 に設定

# 再起動
make down && make up
```

---

### ログの読み方

#### INFO ログ

```
[INFO] Price update: ETH-USD mark_price=3500.00
```

- 通常の動作ログ
- 問題なし

#### WARNING ログ

```
[WARNING] Price approaching order: distance=2.5 bps
```

- 注意が必要な状況
- ロジックが正常に反応している

#### ERROR ログ

```
[ERROR] API request failed: 500 Internal Server Error
```

- エラー発生
- 要対応

**対応優先度:**

1. **Position関連エラー** → 最優先、即停止
2. **API接続エラー** → 再起動で解決する場合が多い
3. **設定エラー** → `.env` 確認

---

## FAQ

### Q1: DRY_RUNモードでどのくらいテストすべきですか？

**A:** 最低でも以下を確認してください：

- 30分以上の連続稼働
- 価格変動時の約定回避動作
- エラーがないこと

### Q2: 本番モードで約定した場合、どうすればいいですか？

**A:** 以下の手順で対応：

1. `make down` で即停止
2. StandX UIで成行クローズ（建玉ゼロに）
3. パラメータ見直し
4. DRY_RUNで再テスト

### Q3: ORDER_SIZEはどのくらいが適切ですか？

**A:** 以下を目安に：

- **最小**: 取引所の最小注文額以上
- **推奨**: 残高の10-20%
- **最大**: 残高の50%以下

例: 残高100 DUSDの場合
- 推奨 ORDER_SIZE: 0.5-1.0

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

### Q7: スリッページで約定することはありますか？

**A:** 指値注文なので、スリッページはありません：

- 指定価格でのみ約定
- 不利な価格では約定しない
- ただし、急激な価格変動で逃げ遅れる可能性はある

### Q8: Maker Pointsはいつ反映されますか？

**A:** StandXの仕様に依存：

- リアルタイムではない
- 数時間〜1日程度の遅延
- StandX UIで確認可能

---

## まとめ

### 安全なテストの流れ

```
✅ Phase 1: 環境準備
  → DUSD入金、設定確認

✅ Phase 2: DRY_RUNテスト
  → 実注文なしで動作確認

✅ Phase 3: 本番起動
  → 慎重に本番開始

✅ Phase 4: 監視・運用
  → 定期チェック、異常検知
```

### 重要な原則

1. **必ずDRY_RUNから開始**
2. **少額からテスト**
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
