#!/usr/bin/env python3
"""BSC (EVM) ウォレットを作成し、.envファイルを生成する."""

import os
import sys
from pathlib import Path

try:
    from eth_account import Account
    from nacl.signing import SigningKey
except ImportError as e:
    print(f"Error: Required library is not installed: {e}")
    print("Install with: pip install eth-account pynacl")
    sys.exit(1)


def create_wallet() -> tuple[str, str, str]:
    """
    新しいBSCウォレットとAPIリクエスト署名用Ed25519鍵を作成.

    Returns:
        tuple[str, str, str]: (private_key_hex, address, request_signing_key_hex)
    """
    # secp256k1鍵ペアを生成（ウォレット用）
    account = Account.create()

    # 秘密鍵を0x付きhex形式で取得
    private_key_hex = "0x" + account.key.hex()

    # アドレスを0x付きhex形式で取得
    address = account.address

    # Ed25519鍵ペアを生成（APIリクエスト署名用）
    signing_key = SigningKey.generate()
    request_signing_key_hex = bytes(signing_key).hex()

    return private_key_hex, address, request_signing_key_hex


def create_env_file(private_key: str, address: str, request_signing_key: str) -> None:
    """
    .envファイルを作成.

    Args:
        private_key: 秘密鍵（0x形式）
        address: ウォレットアドレス（0x形式）
        request_signing_key: APIリクエスト署名用Ed25519秘密鍵（hex形式）
    """
    # プロジェクトルートのパス
    project_root = Path(__file__).parent.parent
    env_example_path = project_root / ".env.example"
    env_path = project_root / ".env"

    # .envが既に存在し、空でない場合は上書きしない
    if env_path.exists():
        # ファイルサイズをチェック
        file_size = env_path.stat().st_size
        if file_size > 0:
            print(f"\n⚠️  .env file already exists: {env_path}")
            print("Will not overwrite existing .env file.")
            print("To create a new wallet, delete .env first: rm .env")
            sys.exit(0)
        # 空ファイルの場合は上書きを許可
        print(f"\n📝 Empty .env file found, will overwrite...")

    # .env.exampleを読み込み
    if not env_example_path.exists():
        print(f"Error: .env.example not found at {env_example_path}")
        sys.exit(1)

    with open(env_example_path) as f:
        content = f.read()

    # 秘密鍵とアドレスを埋め込む
    content = content.replace("STANDX_PRIVATE_KEY=0x...", f"STANDX_PRIVATE_KEY={private_key}")
    content = content.replace(
        "STANDX_WALLET_ADDRESS=0x...", f"STANDX_WALLET_ADDRESS={address}"
    )

    # STANDX_CHAIN を bsc に設定
    content = content.replace("STANDX_CHAIN=solana", "STANDX_CHAIN=bsc")

    # リクエスト署名鍵を埋め込む
    content = content.replace(
        "STANDX_REQUEST_SIGNING_KEY=", f"STANDX_REQUEST_SIGNING_KEY={request_signing_key}"
    )

    # .envファイルを書き込み
    with open(env_path, "w") as f:
        f.write(content)

    # パーミッションを600に設定（所有者のみ読み書き可能）
    os.chmod(env_path, 0o600)

    print(f"\n✅ .env file created: {env_path}")


def main() -> None:
    """メイン処理."""
    print("=" * 60)
    print("BSC Wallet Generator (secp256k1 / EVM)")
    print("=" * 60)

    # ウォレット作成
    print("\n🔐 Generating new BSC wallet...")
    private_key, address, request_signing_key = create_wallet()

    # 結果を表示
    print("\n" + "=" * 60)
    print("⚠️  IMPORTANT: Save this information securely!")
    print("=" * 60)
    print(f"\nWallet Address (0x):              {address}")
    print(f"Private Key (0x):                 {private_key}")
    print(f"Request Signing Key (Ed25519):    {request_signing_key}")
    print("\n" + "=" * 60)
    print("⚠️  Security Warnings:")
    print("=" * 60)
    print("1. NEVER commit .env file to Git")
    print("2. NEVER share your private key")
    print("3. Use this wallet for TESTING ONLY")
    print("4. Keep only small amounts of BNB for transaction fees")
    print("=" * 60)

    # .envファイルを作成
    print("\n📝 Creating .env file...")
    create_env_file(private_key, address, request_signing_key)

    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Deposit small amount of BNB for transaction fees (~0.01 BNB)")
    print("2. Review .env file and adjust settings if needed")
    print("3. Run: make test")
    print()


if __name__ == "__main__":
    main()
