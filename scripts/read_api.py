#!/usr/bin/env python3
"""StandX API読み取りツール（動作確認・デバッグ用）."""

import asyncio
import sys
from datetime import datetime
from typing import Any

import aiohttp
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from standx_mm_bot.client import StandXHTTPClient
from standx_mm_bot.config import Settings


console = Console()

# Solana RPC エンドポイント（メインネット）
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"

# USDC Mint Address (Solana mainnet)
USDC_MINT_ADDRESS = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

# BSC RPC エンドポイント（メインネット）
BSC_RPC_URL = "https://bsc-dataseed.binance.org/"

# USDC Contract Address (BSC mainnet - Binance-Peg BSC-USD)
BSC_USDC_CONTRACT = "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d"


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


async def get_solana_balance(wallet_address: str) -> dict[str, Any]:
    """
    Solanaウォレットの残高を取得.

    Args:
        wallet_address: ウォレットアドレス

    Returns:
        dict: SOL残高とUSDC残高
    """
    async with aiohttp.ClientSession() as session:
        # SOL残高取得
        sol_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [wallet_address]
        }
        async with session.post(SOLANA_RPC_URL, json=sol_payload) as response:
            sol_result = await response.json()
            sol_balance = sol_result.get("result", {}).get("value", 0) / 1e9  # lamports to SOL

        # USDCトークンアカウント取得
        usdc_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                wallet_address,
                {"mint": USDC_MINT_ADDRESS},
                {"encoding": "jsonParsed"}
            ]
        }
        async with session.post(SOLANA_RPC_URL, json=usdc_payload) as response:
            usdc_result = await response.json()
            usdc_accounts = usdc_result.get("result", {}).get("value", [])
            usdc_balance = 0.0
            if usdc_accounts:
                # 最初のアカウントのUSDC残高を取得
                token_amount = usdc_accounts[0]["account"]["data"]["parsed"]["info"]["tokenAmount"]
                usdc_balance = float(token_amount["uiAmount"])

    return {
        "sol": sol_balance,
        "usdc": usdc_balance
    }


async def get_bsc_balance(wallet_address: str) -> dict[str, Any]:
    """
    BSCウォレットの残高を取得.

    Args:
        wallet_address: ウォレットアドレス（0x形式）

    Returns:
        dict: BNB残高とUSDC残高
    """
    async with aiohttp.ClientSession() as session:
        # BNB残高取得
        bnb_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_getBalance",
            "params": [wallet_address, "latest"]
        }
        async with session.post(BSC_RPC_URL, json=bnb_payload) as response:
            bnb_result = await response.json()
            bnb_hex = bnb_result.get("result", "0x0")
            bnb_balance = int(bnb_hex, 16) / 1e18  # Wei to BNB

        # USDC残高取得（ERC-20 balanceOf）
        # balanceOf(address) のシグネチャ: 0x70a08231
        balance_of_signature = "0x70a08231"
        # アドレスを32バイトにパディング
        padded_address = wallet_address[2:].zfill(64)
        data = balance_of_signature + padded_address

        usdc_payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "eth_call",
            "params": [
                {
                    "to": BSC_USDC_CONTRACT,
                    "data": data
                },
                "latest"
            ]
        }
        async with session.post(BSC_RPC_URL, json=usdc_payload) as response:
            usdc_result = await response.json()
            usdc_hex = usdc_result.get("result", "0x0")
            usdc_balance = int(usdc_hex, 16) / 1e18  # USDC decimals

    return {
        "bnb": bnb_balance,
        "usdc": usdc_balance
    }


async def get_balance(client: StandXHTTPClient, wallet_address: str, chain: str = "solana") -> None:
    """残高情報を取得して表示."""
    try:
        # StandX取引所残高
        try:
            standx_balance = await client.get_balance()
        except Exception as e:
            # 404エラー（残高レコードなし）の場合はゼロとして扱う
            if "404" in str(e) or "not found" in str(e).lower():
                console.print("[yellow]⚠️  StandX account has no balance (not deposited yet)[/yellow]")
                standx_balance = {
                    "equity": 0,
                    "cross_available": 0,
                    "upnl": 0,
                    "locked": 0
                }
            else:
                raise

        # チェーン別のウォレット残高取得
        if chain.lower() == "bsc":
            chain_balance = await get_bsc_balance(wallet_address)
            chain_name = "BSC"
            native_token = "BNB"
            native_balance = chain_balance["bnb"]
        else:  # solana
            chain_balance = await get_solana_balance(wallet_address)
            chain_name = "Solana"
            native_token = "SOL"
            native_balance = chain_balance["sol"]

        # StandX残高テーブル
        standx_table = Table(title="💰 StandX Exchange Balance", box=box.ROUNDED)
        standx_table.add_column("Field", style="cyan", no_wrap=True)
        standx_table.add_column("Value", style="green", justify="right")

        equity = float(standx_balance.get("equity", 0))
        available = float(standx_balance.get("cross_available", 0))
        upnl = float(standx_balance.get("upnl", 0))
        locked = float(standx_balance.get("locked", 0))

        standx_table.add_row("Equity (資産額)", f"${equity:,.2f}")
        standx_table.add_row("Available (利用可能額)", f"${available:,.2f}")
        standx_table.add_row("Locked (ロック額)", f"${locked:,.2f}")

        upnl_color = "green" if upnl >= 0 else "red"
        upnl_symbol = "+" if upnl >= 0 else ""
        standx_table.add_row(
            "Unrealized PnL (未実現損益)",
            f"[{upnl_color}]{upnl_symbol}${upnl:,.2f}[/{upnl_color}]"
        )

        console.print(standx_table)
        console.print()

        # チェーン残高テーブル
        chain_table = Table(title=f"🔗 {chain_name} Wallet Balance", box=box.ROUNDED)
        chain_table.add_column("Token", style="cyan", no_wrap=True)
        chain_table.add_column("Balance", style="green", justify="right")

        chain_table.add_row(native_token, f"{native_balance:.4f}")
        chain_table.add_row("USDC", f"${chain_balance['usdc']:,.2f}")

        console.print(chain_table)
        console.print(f"[green]✅ Balance fetched successfully[/green]")

    except Exception as e:
        console.print(f"[red]❌ Error fetching balance: {e}[/red]")
        raise


async def get_status(client: StandXHTTPClient, symbol: str, wallet_address: str, chain: str = "solana") -> None:
    """全ての状態を一括表示."""
    console.print(Panel(
        f"[bold cyan]StandX API Status Check[/bold cyan]\n"
        f"Symbol: {symbol}\n"
        f"Chain: {chain.upper()}\n"
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        box=box.DOUBLE
    ))
    console.print()

    # 残高情報
    await get_balance(client, wallet_address, chain)
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
        console.print("Commands: price, orders, position, balance, status")
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
            elif command == "balance":
                await get_balance(client, config.standx_wallet_address, config.standx_chain)
            elif command == "status":
                await get_status(client, config.symbol, config.standx_wallet_address, config.standx_chain)
            else:
                console.print(f"[red]Unknown command: {command}[/red]")
                console.print("Available commands: price, orders, position, balance, status")
                sys.exit(1)

    except Exception as e:
        console.print(f"[red]❌ Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
