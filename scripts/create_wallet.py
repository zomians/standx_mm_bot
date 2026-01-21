#!/usr/bin/env python3
"""Solanaウォレットを作成し、.envファイルを生成する."""

import os
import sys
from pathlib import Path

try:
    from nacl.signing import SigningKey
    import base58
except ImportError as e:
    print(f"Error: Required library is not installed: {e}")
    print("Install with: pip install pynacl base58")
    sys.exit(1)


def create_wallet() -> tuple[str, str]:
    """
    新しいSolanaウォレットを作成.

    Returns:
        tuple[str, str]: (private_key_hex, address_base58)
    """
    # Ed25519鍵ペアを生成
    signing_key = SigningKey.generate()

    # 秘密鍵（32バイト）をhex形式で取得
    private_key_bytes = bytes(signing_key)
    private_key_hex = private_key_bytes.hex()

    # 公開鍵からSolanaアドレスを生成（Base58エンコード）
    public_key_bytes = bytes(signing_key.verify_key)
    address_base58 = base58.b58encode(public_key_bytes).decode('ascii')

    return private_key_hex, address_base58


def create_env_file(private_key: str, address: str) -> None:
    """
    .envファイルを作成.

    Args:
        private_key: 秘密鍵（hex形式）
        address: ウォレットアドレス（Base58）
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

    # 秘密鍵とアドレスを埋め込む（0xプレフィックスなし、hex形式）
    content = content.replace("STANDX_PRIVATE_KEY=0x...", f"STANDX_PRIVATE_KEY={private_key}")
    content = content.replace(
        "STANDX_WALLET_ADDRESS=0x...", f"STANDX_WALLET_ADDRESS={address}"
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
    print("Solana Wallet Generator (Ed25519)")
    print("=" * 60)

    # ウォレット作成
    print("\n🔐 Generating new Solana wallet...")
    private_key, address = create_wallet()

    # 結果を表示
    print("\n" + "=" * 60)
    print("⚠️  IMPORTANT: Save this information securely!")
    print("=" * 60)
    print(f"\nWallet Address (Base58): {address}")
    print(f"Private Key (hex):       {private_key}")
    print("\n" + "=" * 60)
    print("⚠️  Security Warnings:")
    print("=" * 60)
    print("1. NEVER commit .env file to Git")
    print("2. NEVER share your private key")
    print("3. Use this wallet for TESTING ONLY")
    print("4. Keep only small amounts of SOL for transaction fees")
    print("=" * 60)

    # .envファイルを作成
    print("\n📝 Creating .env file...")
    create_env_file(private_key, address)

    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Deposit small amount of SOL for transaction fees (~0.01 SOL)")
    print("2. Review .env file and adjust settings if needed")
    print("3. Run: make test")
    print()


if __name__ == "__main__":
    main()
