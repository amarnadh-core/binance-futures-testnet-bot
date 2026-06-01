"""Thin wrapper around the python-binance futures client."""

from typing import Any


FUTURES_TESTNET_URL = "https://testnet.binancefuture.com/fapi"


class BinanceClientError(RuntimeError):
    """Raised when Binance communication fails."""


class BinanceTradingClient:
    def __init__(self, api_key: str, api_secret: str) -> None:
        try:
            from binance.client import Client
        except ImportError as exc:
            raise BinanceClientError(
                "python-binance is not installed. Run: pip install -r requirements.txt"
            ) from exc

        self._client = Client(api_key, api_secret, testnet=True)
        # Safety guard: ensure orders are routed to Binance Futures Testnet
        resolved_url = self._client._create_futures_api_uri("order")
        if not resolved_url.startswith(f"{FUTURES_TESTNET_URL}/"):
            raise BinanceClientError(
                f"Refusing to send orders outside Futures Testnet: {resolved_url}"
            )

    def create_futures_order(self, **params: Any) -> dict[str, Any]:
        try:
            return self._client.futures_create_order(**params)
        except Exception as exc:
            raise BinanceClientError(f"Binance API request failed: {exc}") from exc

    def get_futures_order(self, **params: Any) -> dict[str, Any]:
        try:
            return self._client.futures_get_order(**params)
        except Exception as exc:
            raise BinanceClientError(f"Binance API request failed: {exc}") from exc
