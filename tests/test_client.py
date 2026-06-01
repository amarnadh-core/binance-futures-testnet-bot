import sys
from types import ModuleType
import unittest
from unittest.mock import patch

from bot.client import BinanceClientError, BinanceTradingClient


class FakeBinanceClient:
    FUTURES_URL = "https://fapi.binance.com/fapi"
    FUTURES_TESTNET_URL = "https://testnet.binancefuture.com/fapi"

    def __init__(self, api_key, api_secret, testnet=False):
        self.testnet = testnet

    def _create_futures_api_uri(self, path, version=1):
        base_url = self.FUTURES_TESTNET_URL if self.testnet else self.FUTURES_URL
        return f"{base_url}/v{version}/{path}"

    def futures_get_order(self, **params):
        return params


class LiveResolvingBinanceClient(FakeBinanceClient):
    def _create_futures_api_uri(self, path, version=1):
        return f"{self.FUTURES_URL}/v{version}/{path}"


def fake_binance_modules(client_class):
    package = ModuleType("binance")
    client_module = ModuleType("binance.client")
    client_module.Client = client_class
    package.client = client_module
    return {"binance": package, "binance.client": client_module}


class BinanceTradingClientTests(unittest.TestCase):
    def test_accepts_resolved_futures_testnet_endpoint(self):
        with patch.dict(sys.modules, fake_binance_modules(FakeBinanceClient)):
            client = BinanceTradingClient("key", "secret")

        self.assertTrue(client._client.testnet)

    def test_refuses_live_futures_endpoint(self):
        with patch.dict(sys.modules, fake_binance_modules(LiveResolvingBinanceClient)):
            with self.assertRaisesRegex(BinanceClientError, "Refusing"):
                BinanceTradingClient("key", "secret")

    def test_get_futures_order_delegates_to_binance_client(self):
        with patch.dict(sys.modules, fake_binance_modules(FakeBinanceClient)):
            client = BinanceTradingClient("key", "secret")

        self.assertEqual(
            client.get_futures_order(symbol="BTCUSDT", orderId=123),
            {"symbol": "BTCUSDT", "orderId": 123},
        )


if __name__ == "__main__":
    unittest.main()
