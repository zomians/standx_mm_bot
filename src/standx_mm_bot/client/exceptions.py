"""カスタム例外クラス."""


class APIError(Exception):
    """StandX API エラー."""


class AuthenticationError(APIError):
    """認証エラー (401)."""


class NetworkError(APIError):
    """ネットワークエラー."""
