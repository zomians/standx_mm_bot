# Phase 3-1: 距離計算と約定回避の実装ガイド

このガイドでは、Phase 3-1で実装した距離計算（`core/distance.py`）と約定回避（`core/escape.py`）について詳しく解説します。

**対象読者**: Python初心者、Market Making初心者、金融工学の基礎を学びたい方

**関連Issue**: [#16 Phase 3-1: 距離計算と約定回避の実装](https://github.com/zomians/standx_mm_bot/issues/16)

**実装PR**: [#54 Phase 3-1: 距離計算と約定回避の実装](https://github.com/zomians/standx_mm_bot/pull/54)

---

## 目次

1. [概要](#概要)
2. [bps（ベーシスポイント）の基礎](#bpsベーシスポイントの基礎)
3. [core/distance.pyの実装解説](#coredistancepyの実装解説)
4. [core/escape.pyの実装解説](#coreescapepyの実装解説)
5. [テストケース設計のベストプラクティス](#テストケース設計のベストプラクティス)
6. [設計判断の記録](#設計判断の記録)
7. [まとめ](#まとめ)

---

## 概要

### Phase 3-1の目的

Market Making Botにおいて、**約定させずに板に居続ける**ためには、以下の機能が必要です：

1. **距離計算**: 注文が現在価格からどれだけ離れているかを正確に計算
2. **約定回避判定**: 価格が接近してきたら、約定される前に逃げる

Phase 3-1では、この2つの機能を実装しました。

### 実装したモジュール

| モジュール | 責務 | 関数数 |
|-----------|------|--------|
| `core/distance.py` | 距離計算、目標価格計算、接近判定 | 3 |
| `core/escape.py` | 約定回避判定、逃避先価格計算 | 2 |

### なぜ重要なのか

```
約定 = 失敗
```

Market Making Botの目的は**Maker Pointsを獲得すること**であり、約定することではありません。約定すると：

- ❌ 手数料がかかる（テイカー手数料）
- ❌ 建玉を持つ（Funding Rateリスク、清算リスク）
- ❌ 目的から逸脱

そのため、**価格が接近してきたら即座に逃げる**仕組みが必要です。

---

## bps（ベーシスポイント）の基礎

### bpsとは

**bps（basis points, ベーシスポイント）** は、金融業界で使われる単位で、**0.01%（1/10000）** を表します。

```
1 bps = 0.01% = 0.0001 = 1/10000
```

### なぜbpsを使うのか

価格が異なる資産でも**統一的に距離を表現**できるからです。

#### 例：パーセントだと不便

```python
# ETH-USD（価格：$2,500）
注文価格: $2,490
mark_price: $2,500
差額: $10
パーセント: 10 / 2500 = 0.4%

# BTC-USD（価格：$50,000）
注文価格: $49,800
mark_price: $50,000
差額: $200
パーセント: 200 / 50000 = 0.4%
```

パーセントだと「0.4%」で同じですが、**絶対値（ドル）が全く違う**ため、パラメータ設定が困難です。

#### bpsなら統一的

```python
# ETH-USD
距離: 40 bps

# BTC-USD
距離: 40 bps
```

**40 bps = 0.4%** なので、どの資産でも「40 bps以内」という統一的な基準を使えます。

### bpsの計算方法

```python
bps = (価格差 / 基準価格) * 10000
```

#### 例1: ETH-USD

```python
mark_price = 2500.0      # 現在価格
order_price = 2490.0     # 注文価格
差額 = 2500.0 - 2490.0 = 10.0

bps = (10.0 / 2500.0) * 10000 = 40.0 bps
```

#### 例2: BTC-USD

```python
mark_price = 50000.0
order_price = 49800.0
差額 = 50000.0 - 49800.0 = 200.0

bps = (200.0 / 50000.0) * 10000 = 40.0 bps
```

どちらも **40 bps** で統一されています。

### StandX MM Botでのbps基準

| パラメータ | デフォルト値 | 意味 |
|-----------|------------|------|
| `target_distance_bps` | 8 bps | 目標距離（報酬をもらえる10bps以内に配置） |
| `escape_threshold_bps` | 3 bps | 約定回避距離（これ以下なら逃げる） |
| `outer_escape_distance_bps` | 15 bps | 逃避先距離（逃げる先） |

---

## core/distance.pyの実装解説

`core/distance.py`は、距離計算に関する3つの関数を提供します。

### 1. calculate_distance_bps()

#### 機能

注文価格と現在価格（mark_price）の距離をbpsで計算します。

#### 実装

```python
def calculate_distance_bps(order_price: float, mark_price: float) -> float:
    """注文と mark_price の距離を bps で計算."""
    return abs(order_price - mark_price) / mark_price * 10000
```

#### 数学的根拠

```
distance_bps = |order_price - mark_price| / mark_price * 10000

絶対値を使う理由：
- BUY注文: order_price < mark_price（下側）
- SELL注文: order_price > mark_price（上側）
→ どちらも「距離」として正の値で統一
```

#### 使用例

```python
from standx_mm_bot.core.distance import calculate_distance_bps

mark_price = 2500.0
buy_order_price = 2490.0  # 10ドル下

distance = calculate_distance_bps(buy_order_price, mark_price)
print(distance)  # 40.0 bps
```

#### テストケース

```python
def test_calculate_distance_bps():
    # 基本計算
    assert calculate_distance_bps(2490.0, 2500.0) == pytest.approx(40.0)

    # ゼロ距離
    assert calculate_distance_bps(2500.0, 2500.0) == pytest.approx(0.0)

    # 負の値も正の値になる（絶対値）
    assert calculate_distance_bps(2510.0, 2500.0) == pytest.approx(40.0)
```

---

### 2. calculate_target_price()

#### 機能

指定した距離（bps）に配置する目標価格を計算します。

#### 実装

```python
def calculate_target_price(mark_price: float, side: Side, distance_bps: float) -> float:
    """目標価格を計算."""
    offset = mark_price * (distance_bps / 10000)
    if side == Side.BUY:
        return mark_price - offset  # 下側
    else:
        return mark_price + offset  # 上側
```

#### ロジック

```
BUY注文（買い指値）:
  target_price = mark_price - (mark_price * distance_bps / 10000)
  → 現在価格より「下」に配置

SELL注文（売り指値）:
  target_price = mark_price + (mark_price * distance_bps / 10000)
  → 現在価格より「上」に配置
```

#### 図解

```
SELL注文: 現在価格より上
  2502.0 ─────────────── SELL (8bps上)
             ↑
             | +8bps
             |
  2500.0 ─────────────── mark_price
             |
             | -8bps
             ↓
  2498.0 ─────────────── BUY (8bps下)
BUY注文: 現在価格より下
```

#### 使用例

```python
from standx_mm_bot.core.distance import calculate_target_price
from standx_mm_bot.models import Side

mark_price = 2500.0
target_distance = 8.0  # 8bps

# BUY注文の目標価格
buy_target = calculate_target_price(mark_price, Side.BUY, target_distance)
print(buy_target)  # 2498.0 (2500 - 2500*0.0008)

# SELL注文の目標価格
sell_target = calculate_target_price(mark_price, Side.SELL, target_distance)
print(sell_target)  # 2502.0 (2500 + 2500*0.0008)
```

#### テストケース

```python
def test_calculate_target_price_buy():
    target = calculate_target_price(2500.0, Side.BUY, 8.0)
    assert target == pytest.approx(2498.0)

def test_calculate_target_price_sell():
    target = calculate_target_price(2500.0, Side.SELL, 8.0)
    assert target == pytest.approx(2502.0)
```

---

### 3. is_approaching()

#### 機能

価格が注文に接近しているか（約定の危険があるか）を判定します。

#### 実装

```python
def is_approaching(mark_price: float, order_price: float, side: Side) -> bool:
    """価格が注文に接近しているか判定."""
    if side == Side.BUY:
        return mark_price < order_price  # 価格が下がっている
    else:
        return mark_price > order_price  # 価格が上がっている
```

#### 設計思想：なぜこの判定なのか

##### BUY注文の場合

```
BUY注文（買い指値）は「この価格以下で買いたい」

  2500 ──────────── mark_price（上がっている）
             ↑
             | is_approaching() = False
             | 価格が上がる = 約定しない = 安全
             |
  2498 ──────────── BUY order_price
             |
             | is_approaching() = True
             | 価格が下がる = 約定の危険 = 逃げる！
             ↓
  2497 ──────────── mark_price（下がっている）
```

**判定条件**: `mark_price < order_price`

- mark_priceが注文価格より**下**にある
- → 約定される可能性が高い
- → **接近している**（危険）

##### SELL注文の場合

```
SELL注文（売り指値）は「この価格以上で売りたい」

  2503 ──────────── mark_price（上がっている）
             ↑
             | is_approaching() = True
             | 価格が上がる = 約定の危険 = 逃げる！
             |
  2502 ──────────── SELL order_price
             |
             | is_approaching() = False
             | 価格が下がる = 約定しない = 安全
             ↓
  2500 ──────────── mark_price（下がっている）
```

**判定条件**: `mark_price > order_price`

- mark_priceが注文価格より**上**にある
- → 約定される可能性が高い
- → **接近している**（危険）

#### 使用例

```python
from standx_mm_bot.core.distance import is_approaching
from standx_mm_bot.models import Side

order_price = 2498.0  # BUY注文

# ケース1: 価格が下がっている（接近）
mark_price = 2497.0
print(is_approaching(mark_price, order_price, Side.BUY))  # True

# ケース2: 価格が上がっている（離れている）
mark_price = 2501.0
print(is_approaching(mark_price, order_price, Side.BUY))  # False
```

#### テストケース

```python
def test_buy_approaching():
    """BUY注文: 価格が注文価格より下 = 接近"""
    order_price = 2498.0

    # mark_price < order_price → 接近（危険）
    assert is_approaching(2497.0, order_price, Side.BUY) is True
    assert is_approaching(2490.0, order_price, Side.BUY) is True

def test_buy_not_approaching():
    """BUY注文: 価格が注文価格より上 = 離れている"""
    order_price = 2498.0

    # mark_price > order_price → 離れている（安全）
    assert is_approaching(2500.0, order_price, Side.BUY) is False
    assert is_approaching(2501.0, order_price, Side.BUY) is False
```

---

## core/escape.pyの実装解説

`core/escape.py`は、約定回避に関する2つの関数を提供します。

### 1. should_escape()

#### 機能

約定回避が必要か判定します。**2段階チェック**を実施します。

#### 実装

```python
def should_escape(
    mark_price: float,
    order_price: float,
    side: Side,
    escape_threshold_bps: float,
) -> bool:
    """約定回避が必要か判定."""
    # 優先順位1: 価格が接近しているかチェック
    if not is_approaching(mark_price, order_price, side):
        return False

    # 優先順位2: 距離が escape_threshold_bps 未満かチェック
    distance = calculate_distance_bps(order_price, mark_price)
    return distance < escape_threshold_bps
```

#### 2段階チェックの理由

##### チェック1: 価格が接近しているか

```python
if not is_approaching(mark_price, order_price, side):
    return False
```

**理由**: 価格が**離れている方向**に動いている場合、どれだけ近くても逃げる必要はない。

**例（BUY注文）**:

```
order_price = 2498.0
mark_price = 2499.0  # 注文から1bps（非常に近い）

しかし、mark_price > order_price
→ 価格が上がっている = 約定しない = 逃げなくてOK
```

##### チェック2: 距離がしきい値未満か

```python
distance = calculate_distance_bps(order_price, mark_price)
return distance < escape_threshold_bps
```

**理由**: 価格が接近している方向でも、**まだ距離がある**なら急いで逃げる必要はない。

**例（BUY注文）**:

```
order_price = 2498.0
mark_price = 2490.0  # 注文より下（接近方向）

距離 = 32 bps
escape_threshold = 3 bps

32 bps > 3 bps → まだ余裕がある = 逃げなくてOK
```

#### 判定フローチャート

```
should_escape() の判定フロー

価格更新を受信
    ↓
is_approaching() チェック
    ├─ False → 約定回避不要（離れている）
    └─ True → 次へ
         ↓
距離 < escape_threshold_bps ?
    ├─ False → 約定回避不要（まだ余裕あり）
    └─ True → 約定回避必要（逃げる！）
```

#### 使用例

```python
from standx_mm_bot.core.escape import should_escape
from standx_mm_bot.models import Side

order_price = 2498.0  # BUY注文
escape_threshold = 3.0  # 3bps

# ケース1: 接近 & しきい値以内 → 逃げる
mark_price = 2497.5  # 注文より下、約2bps
print(should_escape(mark_price, order_price, Side.BUY, escape_threshold))  # True

# ケース2: 接近しているがしきい値外 → 逃げない
mark_price = 2490.0  # 注文より下、約32bps
print(should_escape(mark_price, order_price, Side.BUY, escape_threshold))  # False

# ケース3: 離れている → 逃げない
mark_price = 2500.0  # 注文より上
print(should_escape(mark_price, order_price, Side.BUY, escape_threshold))  # False
```

#### テストケース

```python
def test_buy_approaching_within_threshold():
    """BUY注文: 接近 & しきい値以内 → True"""
    mark_price = 2497.5  # order_priceより下
    order_price = 2498.0
    escape_threshold = 3.0

    # 距離: 約2bps < 3bps かつ mark_price < order_price
    assert should_escape(mark_price, order_price, Side.BUY, escape_threshold) is True

def test_buy_approaching_outside_threshold():
    """BUY注文: 接近しているがしきい値外 → False"""
    mark_price = 2490.0
    order_price = 2498.0
    escape_threshold = 3.0

    # 距離: 約32bps > 3bps（まだ余裕）
    assert should_escape(mark_price, order_price, Side.BUY, escape_threshold) is False
```

---

### 2. calculate_escape_price()

#### 機能

約定回避時に逃げる先の価格を計算します。

#### 実装

```python
def calculate_escape_price(
    mark_price: float,
    side: Side,
    outer_escape_distance_bps: float,
) -> float:
    """逃避先価格を計算."""
    return calculate_target_price(mark_price, side, outer_escape_distance_bps)
```

#### ロジック

`calculate_target_price()`を利用して、現在の`mark_price`から指定した距離（デフォルト15bps）の位置を計算します。

```
逃避先 = 現在のmark_priceから outer_escape_distance_bps 離れた位置
```

**なぜ新しいmark_priceから計算するのか**:

- 注文配置時のmark_priceは古い
- 約定回避時は**最新のmark_price**から安全な距離に逃げる

#### 図解

```
BUY注文の約定回避

初期状態:
  2500.0 ──────────── 初期mark_price
  2498.0 ──────────── BUY order (8bps)

価格が下落:
  2497.5 ──────────── 新mark_price（接近！）
             ↓
         約定回避発動
             ↓
  2493.75 ─────────── 逃避先 (15bps下)
  ↑ calculate_escape_price(2497.5, BUY, 15.0)
```

#### 使用例

```python
from standx_mm_bot.core.escape import calculate_escape_price
from standx_mm_bot.models import Side

# 価格が下落して接近
new_mark_price = 2497.5
outer_distance = 15.0  # 15bps

# 逃避先を計算
escape_price = calculate_escape_price(new_mark_price, Side.BUY, outer_distance)
print(escape_price)  # 2493.75（2497.5 - 2497.5*0.0015）
```

#### テストケース

```python
def test_buy_escape_price():
    mark_price = 2500.0
    outer_distance = 15.0

    escape_price = calculate_escape_price(mark_price, Side.BUY, outer_distance)

    # 2500 - (2500 * 0.0015) = 2496.25
    assert escape_price == pytest.approx(2496.25)
```

---

## テストケース設計のベストプラクティス

Phase 3-1では、**31個のテストケース**を実装しました。テストケース設計の考え方を解説します。

### 1. 基本計算テスト

**目的**: 関数が期待通りに動作することを確認

```python
def test_basic_calculation():
    # 10 / 2500 * 10000 = 40bps
    assert calculate_distance_bps(2490.0, 2500.0) == pytest.approx(40.0)
```

**ポイント**:
- 手計算で検証可能な値を使う
- `pytest.approx()`で浮動小数点誤差を許容

---

### 2. 境界値テスト

**目的**: エッジケースを検証

```python
def test_zero_distance():
    """距離がゼロの場合"""
    assert calculate_distance_bps(2500.0, 2500.0) == pytest.approx(0.0)

def test_small_distance():
    """小さい距離（1bps, 5bps, 10bps）"""
    mark_price = 2500.0

    # 1bps
    order_price_1bps = 2500.0 - (2500.0 * 0.0001)
    assert calculate_distance_bps(order_price_1bps, mark_price) == pytest.approx(1.0)

def test_large_distance():
    """大きい距離（100bps, 1000bps）"""
    # ...
```

**ポイント**:
- 最小値（0）、最大値（実用的な範囲）をテスト
- 典型的な値（1bps, 5bps, 10bps, 100bps）をテスト

---

### 3. 統合シナリオテスト

**目的**: 複数の関数が連携して動作することを確認

```python
def test_approaching_scenario():
    """約定回避シナリオ: 価格が接近してきた場合"""
    mark_price = 2500.0
    escape_threshold = 3.0

    # 1. 注文を8bpsに配置
    buy_order_price = calculate_target_price(mark_price, Side.BUY, 8.0)
    assert buy_order_price == pytest.approx(2498.0)

    # 2. 価格が下がり、接近
    new_mark_price = 2497.5

    # 3. 接近判定
    assert is_approaching(new_mark_price, buy_order_price, Side.BUY) is True

    # 4. 距離計算
    distance = calculate_distance_bps(buy_order_price, new_mark_price)
    assert distance < escape_threshold
```

**ポイント**:
- 実際の使用フローをシミュレート
- 各ステップで中間結果を検証

---

### 4. エッジケーステスト

**目的**: しきい値ちょうどの場合など、微妙なケースを検証

```python
def test_edge_case_exact_threshold():
    """距離がしきい値ちょうどの場合"""
    escape_threshold = 3.0
    order_price = 2500.0

    # mark_priceが注文価格より3bps下（ちょうどしきい値）
    mark_price = calculate_target_price(order_price, Side.BUY, 3.0)
    assert mark_price == pytest.approx(2497.5)

    # 距離がちょうど3bps → しきい値未満ではない → 約定回避不要
    result = should_escape(mark_price, order_price, Side.BUY, escape_threshold)
    assert result is False

    # 少し近い位置（約2bps）→ しきい値未満 → 約定回避必要
    closer_mark_price = 2499.5
    result = should_escape(closer_mark_price, order_price, Side.BUY, escape_threshold)
    assert result is True
```

**ポイント**:
- `<`（未満）vs `<=`（以下）の違いを検証
- オフバイワンエラーを防ぐ

---

### テストカバレッジ

```
src/standx_mm_bot/core/distance.py   100%
src/standx_mm_bot/core/escape.py     100%
```

**すべての行、すべての分岐**をテストでカバーしました。

---

## 設計判断の記録

### なぜdistance.pyとescape.pyを分離したのか

#### 責務の分離

- **distance.py**: 純粋な数学的計算（距離、目標価格、接近判定）
- **escape.py**: ビジネスロジック（約定回避判定、逃避先計算）

#### メリット

1. **テストしやすい**: 各関数が独立してテスト可能
2. **再利用しやすい**: distance.pyの関数は他の用途でも利用可能
3. **理解しやすい**: 各ファイルの責務が明確

---

### なぜis_approaching()が必要なのか

#### 素朴な疑問

「距離だけで判定すればいいのでは？」

```python
# 素朴な実装
def should_escape_simple(order_price, mark_price, threshold):
    distance = calculate_distance_bps(order_price, mark_price)
    return distance < threshold
```

#### 問題点

**価格の方向を考慮していない**

```
BUY注文: 2498.0
mark_price: 2499.0
距離: 約4bps < 5bps → 逃げる？

しかし、mark_price > order_price
→ 価格が上がっている = 約定しない = 逃げる必要なし
```

#### 解決策

**is_approaching()で価格の方向を判定してから、距離をチェック**

```python
# 正しい実装
def should_escape(order_price, mark_price, side, threshold):
    # 1. 価格が接近しているか
    if not is_approaching(mark_price, order_price, side):
        return False

    # 2. 距離がしきい値未満か
    distance = calculate_distance_bps(order_price, mark_price)
    return distance < threshold
```

---

### なぜ絶対値（abs）を使うのか

#### calculate_distance_bps()の実装

```python
return abs(order_price - mark_price) / mark_price * 10000
```

#### 理由

**BUYとSELLで符号が逆**だから統一する必要がある。

```
BUY注文:
  order_price < mark_price
  order_price - mark_price < 0（負）

SELL注文:
  order_price > mark_price
  order_price - mark_price > 0（正）
```

絶対値を使うことで、**常に正の距離**として統一できます。

---

### テストケース設計の工夫

#### 1. クラスで分類

```python
class TestCalculateDistanceBps:
    """calculate_distance_bps のテスト"""
    def test_basic_calculation(): ...
    def test_zero_distance(): ...

class TestCalculateTargetPrice:
    """calculate_target_price のテスト"""
    def test_buy_side(): ...
    def test_sell_side(): ...
```

**メリット**: テストの構造が一目瞭然

#### 2. docstringで意図を明記

```python
def test_buy_approaching():
    """BUY注文: 価格が注文価格より下 = 接近"""
```

**メリット**: テストの失敗時に何をテストしていたか分かる

#### 3. 統合シナリオで実用性を検証

```python
def test_buy_escape_scenario():
    """BUY注文の約定回避シナリオ.

    1. 注文を8bpsに配置
    2. 価格が注文価格を下回り3bps以内に接近
    3. 約定回避判定 → True
    4. 15bpsの逃避先価格を計算
    """
```

**メリット**: 実際の使用フローで動作することを保証

---

## まとめ

### Phase 3-1で学んだこと

1. **bps（ベーシスポイント）**: 金融業界の標準単位
2. **距離計算**: 資産に依存しない統一的な距離表現
3. **約定回避**: 価格の方向と距離の両方を考慮する必要性
4. **テスト設計**: 基本・境界値・統合・エッジケースの網羅

### 実装の要点

| 関数 | 責務 | 重要ポイント |
|------|------|------------|
| `calculate_distance_bps()` | 距離計算 | 絶対値で統一 |
| `calculate_target_price()` | 目標価格計算 | BUY/SELLで方向が逆 |
| `is_approaching()` | 接近判定 | 価格の方向を判定 |
| `should_escape()` | 約定回避判定 | 2段階チェック |
| `calculate_escape_price()` | 逃避先計算 | 最新mark_priceから計算 |

### 次のステップ

Phase 3-2では、**注文管理（core/order.py）** を実装します。

- OrderManager クラス
- 注文発注ロジック（ALO, post_only）
- 注文キャンセルロジック
- 再配置ロジック（発注先行、キャンセル後）

---

## 参考資料

- [DESIGN.md](../../DESIGN.md) - Bot実装設計書
- [GUIDE.md](../../GUIDE.md) - 理論的背景・技術基礎
- [Issue #16](https://github.com/zomians/standx_mm_bot/issues/16) - Phase 3-1の要件定義
- [PR #54](https://github.com/zomians/standx_mm_bot/pull/54) - Phase 3-1の実装

---

**Last Updated**: 2026-01-21
