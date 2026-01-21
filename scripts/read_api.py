#!/usr/bin/env python3
"""StandX API読み取りツール（動作確認・デバッグ用）."""

import asyncio
import sys
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from standx_mm_bot.client import StandXHTTPClient
from standx_mm_bot.config import Settings


console = Console()


async def get_price(client: StandXHTTPClient, symbol: str) -> None:
    """価格情報を取得して表示."""
    try:
        response = await client.get_symbol_price(symbol)

        table = Table(title=f"💰 Price Information", box=box.ROUNDED)
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        table.add_row("Symbol", response.get("symbol", "N/A"))
        table.add_row("Mark Price", f"${float(response.get('mark_price', 0)):,.2f}")
        table.add_row("Index Price", f"${float(response.get('index_price', 0)):,.2f}")

        if "last_price" in response:
            table.add_row("Last Price", f"${float(response['last_price']):,.2f}")

        table.add_row("Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        console.print(table)
        console.print(f"[green]✅ Price fetched successfully[/green]")

    except Exception as e:
        console.print(f"[red]❌ Error fetching price: {e}[/red]")
        raise


async def get_orders(client: StandXHTTPClient, symbol: str) -> None:
    """未決注文一覧を取得して表示."""
    try:
        response = await client.get_open_orders(symbol)
        orders = response.get("result") or response.get("data", [])

        if not orders:
            console.print(Panel(
                "[yellow]No open orders[/yellow]",
                title="📋 Open Orders",
                box=box.ROUNDED
            ))
            return

        table = Table(title=f"📋 Open Orders ({len(orders)})", box=box.ROUNDED)
        table.add_column("Order ID", style="cyan", no_wrap=True)
        table.add_column("Side", style="magenta")
        table.add_column("Price", style="yellow", justify="right")
        table.add_column("Size", style="blue", justify="right")
        table.add_column("Status", style="green")

        for order in orders:
            order_id = str(order.get("order_id", "N/A"))[:12] + "..."
            side = order.get("side", "N/A").upper()
            side_style = "[green]" if side == "BUY" else "[red]"
            price = f"${float(order.get('price', 0)):,.2f}"
            size = f"{float(order.get('qty', 0)):.4f}"
            status = order.get("status", "N/A")

            table.add_row(
                order_id,
                f"{side_style}{side}[/{side_style.strip('[]')}]",
                price,
                size,
                status
            )

        console.print(table)
        console.print(f"[green]✅ {len(orders)} open order(s) found[/green]")

    except Exception as e:
        console.print(f"[red]❌ Error fetching orders: {e}[/red]")
        raise


async def get_position(client: StandXHTTPClient, symbol: str) -> None:
    """ポジション情報を取得して表示."""
    try:
        response = await client.get_position(symbol)

        # レスポンスがリストの場合（ポジションなし）
        if isinstance(response, list):
            if len(response) == 0:
                console.print(Panel(
                    "[yellow]No open positions[/yellow]",
                    title="📊 Position",
                    box=box.ROUNDED
                ))
                return
            # リストの最初の要素を取得
            position = response[0]
        else:
            position = response

        table = Table(title="📊 Position Information", box=box.ROUNDED)
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        # ポジションサイズ
        size = float(position.get("size", 0))
        if size == 0:
            console.print(Panel(
                "[yellow]No open positions (size = 0)[/yellow]",
                title="📊 Position",
                box=box.ROUNDED
            ))
            return

        # ポジション情報表示
        side = "LONG" if size > 0 else "SHORT"
        side_color = "green" if size > 0 else "red"

        table.add_row("Symbol", position.get("symbol", "N/A"))
        table.add_row("Side", f"[{side_color}]{side}[/{side_color}]")
        table.add_row("Size", f"{abs(size):.4f}")

        if "entry_price" in position:
            table.add_row("Entry Price", f"${float(position['entry_price']):,.2f}")

        if "mark_price" in position:
            table.add_row("Mark Price", f"${float(position['mark_price']):,.2f}")

        if "unrealized_pnl" in position:
            pnl = float(position["unrealized_pnl"])
            pnl_color = "green" if pnl >= 0 else "red"
            pnl_symbol = "+" if pnl >= 0 else ""
            table.add_row("Unrealized PnL", f"[{pnl_color}]{pnl_symbol}${pnl:,.2f}[/{pnl_color}]")

        console.print(table)
        console.print(f"[green]✅ Position fetched successfully[/green]")

    except Exception as e:
        console.print(f"[red]❌ Error fetching position: {e}[/red]")
        raise


async def get_status(client: StandXHTTPClient, symbol: str) -> None:
    """全ての状態を一括表示."""
    console.print(Panel(
        f"[bold cyan]StandX API Status Check[/bold cyan]\n"
        f"Symbol: {symbol}\n"
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        box=box.DOUBLE
    ))
    console.print()

    # 価格情報
    await get_price(client, symbol)
    console.print()

    # 未決注文
    await get_orders(client, symbol)
    console.print()

    # ポジション
    await get_position(client, symbol)


async def main() -> None:
    """メイン処理."""
    if len(sys.argv) < 2:
        console.print("[red]Usage: python read_api.py <command>[/red]")
        console.print("Commands: price, orders, position, status")
        sys.exit(1)

    command = sys.argv[1].lower()

    try:
        # 設定読み込み
        config = Settings()

        # dry_runを無効化（実際のAPIから読み取る）
        config.dry_run = False

        async with StandXHTTPClient(config) as client:
            if command == "price":
                await get_price(client, config.symbol)
            elif command == "orders":
                await get_orders(client, config.symbol)
            elif command == "position":
                await get_position(client, config.symbol)
            elif command == "status":
                await get_status(client, config.symbol)
            else:
                console.print(f"[red]Unknown command: {command}[/red]")
                console.print("Available commands: price, orders, position, status")
                sys.exit(1)

    except Exception as e:
        console.print(f"[red]❌ Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
