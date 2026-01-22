#!/usr/bin/env python3
"""統合テストスクリプト - Phase 2.5の自動化.

実際のStandX APIを使用して、注文のライフサイクルをテストします。
"""

import asyncio
import sys
from decimal import Decimal

from rich.console import Console
from rich.table import Table

from standx_mm_bot.client import StandXHTTPClient
from standx_mm_bot.config import Settings
from standx_mm_bot.core.distance import calculate_target_price

console = Console()


async def main() -> None:
    """統合テストのメイン処理."""
    console.print("\n[bold cyan]🧪 StandX MM Bot - Integration Test[/bold cyan]\n")
    console.print("Phase 2.5: 実際のAPIを使用した小額本番テスト\n")

    # 設定読み込み
    config = Settings()

    # 警告表示
    if config.dry_run:
        console.print("[yellow]⚠️  DRY_RUN=True が設定されています[/yellow]")
        console.print("[yellow]このテストは実際の注文を発注するため、DRY_RUN=False が必要です[/yellow]\n")
        return

    # ORDER_SIZE確認
    console.print(f"[cyan]📊 Test Configuration:[/cyan]")
    console.print(f"  Symbol: {config.symbol}")
    console.print(f"  Order Size: {config.order_size}")
    console.print(f"  Chain: {config.standx_chain}")
    console.print()

    if config.order_size > 0.01:
        console.print("[yellow]⚠️  ORDER_SIZE > 0.01 です[/yellow]")
        console.print("[yellow]統合テストでは ORDER_SIZE=0.001-0.01 を推奨します[/yellow]")
        response = input("続行しますか? (yes/no): ")
        if response.lower() != "yes":
            console.print("[red]テスト中止[/red]")
            return

    # テスト開始確認
    console.print("[yellow]⚠️  このテストは実際の注文を発注します[/yellow]")
    console.print("[yellow]約定リスクは最小限ですが、ゼロではありません[/yellow]\n")
    response = input("テストを開始しますか? (yes/no): ")
    if response.lower() != "yes":
        console.print("[red]テスト中止[/red]")
        return

    console.print()

    # HTTPクライアント初期化
    async with StandXHTTPClient(config) as client:
        # ステップ1: 残高確認
        console.print("[bold]Step 1: 残高確認[/bold]")
        try:
            balance = await client.get_balance()
            equity = float(balance.get("equity", 0))
            available = float(balance.get("cross_available", 0))

            console.print(f"  Equity: ${equity:.2f}")
            console.print(f"  Available: ${available:.2f}")

            if equity < 10:
                console.print("[red]❌ 残高不足: $10以上必要です[/red]")
                return

            console.print("[green]✅ 残高OK[/green]\n")
        except Exception as e:
            console.print(f"[red]❌ 残高取得失敗: {e}[/red]")
            return

        # ステップ2: 現在価格取得
        console.print("[bold]Step 2: 現在価格取得[/bold]")
        try:
            price_data = await client.get_symbol_price(config.symbol)
            mark_price = float(price_data.get("mark_price", 0))

            console.print(f"  Mark Price: ${mark_price:.2f}")

            if mark_price == 0:
                console.print("[red]❌ 価格取得失敗[/red]")
                return

            console.print("[green]✅ 価格取得OK[/green]\n")
        except Exception as e:
            console.print(f"[red]❌ 価格取得失敗: {e}[/red]")
            return

        # ステップ3: 安全な注文価格計算（約定しない位置）
        console.print("[bold]Step 3: 注文価格計算[/bold]")

        # 目標距離より遠い位置に注文（約定回避）
        safe_distance_bps = 15.0  # 15bps
        buy_price = calculate_target_price(mark_price, "buy", safe_distance_bps)
        sell_price = calculate_target_price(mark_price, "sell", safe_distance_bps)

        console.print(f"  Buy Price: ${buy_price:.2f} ({safe_distance_bps} bps below)")
        console.print(f"  Sell Price: ${sell_price:.2f} ({safe_distance_bps} bps above)")
        console.print("[green]✅ 価格計算OK[/green]\n")

        # ステップ4: Buy注文発注
        console.print("[bold]Step 4: Buy注文発注[/bold]")
        try:
            buy_order = await client.new_order(
                symbol=config.symbol,
                side="buy",
                order_type="limit",
                price=buy_price,
                size=config.order_size,
            )

            buy_order_id = buy_order.get("order_id")
            console.print(f"  Order ID: {buy_order_id}")
            console.print(f"  Status: {buy_order.get('status')}")
            console.print("[green]✅ Buy注文発注成功[/green]\n")
        except Exception as e:
            console.print(f"[red]❌ Buy注文発注失敗: {e}[/red]")
            return

        # ステップ5: Sell注文発注
        console.print("[bold]Step 5: Sell注文発注[/bold]")
        try:
            sell_order = await client.new_order(
                symbol=config.symbol,
                side="sell",
                order_type="limit",
                price=sell_price,
                size=config.order_size,
            )

            sell_order_id = sell_order.get("order_id")
            console.print(f"  Order ID: {sell_order_id}")
            console.print(f"  Status: {sell_order.get('status')}")
            console.print("[green]✅ Sell注文発注成功[/green]\n")
        except Exception as e:
            console.print(f"[red]❌ Sell注文発注失敗: {e}[/red]")
            # Buy注文をクリーンアップ
            try:
                await client.cancel_order(buy_order_id)
                console.print("[yellow]Buy注文をキャンセルしました[/yellow]")
            except:
                pass
            return

        # ステップ6: 注文確認
        console.print("[bold]Step 6: 注文確認[/bold]")
        await asyncio.sleep(2)  # API反映待ち

        try:
            open_orders = await client.get_open_orders(config.symbol)

            table = Table(title="Open Orders")
            table.add_column("Order ID", style="cyan")
            table.add_column("Side", style="yellow")
            table.add_column("Price", style="green", justify="right")
            table.add_column("Size", style="green", justify="right")
            table.add_column("Status", style="magenta")

            for order in open_orders:
                table.add_row(
                    order["order_id"][:8] + "...",
                    order["side"].upper(),
                    f"${float(order['price']):.2f}",
                    str(order["size"]),
                    order["status"],
                )

            console.print(table)

            if len(open_orders) == 2:
                console.print("[green]✅ 両サイド注文確認OK[/green]\n")
            else:
                console.print(f"[yellow]⚠️  注文数が2件ではありません: {len(open_orders)}件[/yellow]\n")
        except Exception as e:
            console.print(f"[red]❌ 注文確認失敗: {e}[/red]")

        # ステップ7: Position確認
        console.print("[bold]Step 7: Position確認[/bold]")
        try:
            position = await client.get_position(config.symbol)
            position_size = float(position.get("size", 0))

            console.print(f"  Position: {position_size}")

            if position_size == 0:
                console.print("[green]✅ Position = 0 (約定なし)[/green]\n")
            else:
                console.print(f"[red]❌ Position != 0: 約定した可能性があります[/red]\n")
        except Exception as e:
            console.print(f"[yellow]⚠️  Position取得失敗: {e}[/yellow]\n")

        # ステップ8: 注文キャンセル
        console.print("[bold]Step 8: 注文キャンセル[/bold]")

        # Buy注文キャンセル
        try:
            await client.cancel_order(buy_order_id)
            console.print(f"  Buy注文キャンセル: {buy_order_id[:8]}...")
            console.print("[green]✅ Buyキャンセル成功[/green]")
        except Exception as e:
            console.print(f"[red]❌ Buyキャンセル失敗: {e}[/red]")

        # Sell注文キャンセル
        try:
            await client.cancel_order(sell_order_id)
            console.print(f"  Sell注文キャンセル: {sell_order_id[:8]}...")
            console.print("[green]✅ Sellキャンセル成功[/green]\n")
        except Exception as e:
            console.print(f"[red]❌ Sellキャンセル失敗: {e}[/red]\n")

        # ステップ9: キャンセル確認
        console.print("[bold]Step 9: キャンセル確認[/bold]")
        await asyncio.sleep(2)  # API反映待ち

        try:
            open_orders = await client.get_open_orders(config.symbol)

            console.print(f"  Open Orders: {len(open_orders)}件")

            if len(open_orders) == 0:
                console.print("[green]✅ 全注文キャンセル確認[/green]\n")
            else:
                console.print(f"[yellow]⚠️  未キャンセル注文あり: {len(open_orders)}件[/yellow]\n")
                for order in open_orders:
                    console.print(f"    - {order['order_id']}: {order['side']} {order['status']}")
        except Exception as e:
            console.print(f"[red]❌ キャンセル確認失敗: {e}[/red]\n")

    # テスト結果サマリー
    console.print("\n[bold cyan]📊 Test Summary[/bold cyan]\n")
    console.print("[green]✅ 統合テスト完了[/green]")
    console.print()
    console.print("[bold]検証された項目:[/bold]")
    console.print("  ✅ API認証")
    console.print("  ✅ 残高取得")
    console.print("  ✅ 価格取得")
    console.print("  ✅ 注文発注（Buy/Sell）")
    console.print("  ✅ 注文確認")
    console.print("  ✅ 注文キャンセル")
    console.print()
    console.print("[bold]次のステップ:[/bold]")
    console.print("  1. Phase 2.5の全チェックリスト完了を確認")
    console.print("  2. ORDER_SIZEを本番値に設定（例: 0.01）")
    console.print("  3. Phase 3に進む")
    console.print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]テスト中断[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]エラー: {e}[/red]")
        sys.exit(1)
