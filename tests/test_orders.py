import logging
import unittest

from bot.orders import OrderRequest, OrderService
from bot.validators import ValidationError


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.params = None

    def create_futures_order(self, **params):
        self.params = params
        return self.response


class OrderRequestTests(unittest.TestCase):
    def test_market_order_normalizes_values(self):
        order = OrderRequest.from_values("btcusdt", "buy", "market", "0.010")

        self.assertEqual(
            order.to_api_params(),
            {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "MARKET",
                "quantity": "0.010",
            },
        )

    def test_limit_order_includes_price_and_gtc(self):
        order = OrderRequest.from_values("ethusdt", "sell", "limit", "1", "2500.50")

        self.assertEqual(order.to_api_params()["timeInForce"], "GTC")
        self.assertEqual(order.to_api_params()["price"], "2500.50")

    def test_limit_order_requires_price(self):
        with self.assertRaisesRegex(ValidationError, "Price is required"):
            OrderRequest.from_values("BTCUSDT", "BUY", "LIMIT", "0.01")

    def test_quantity_must_be_positive(self):
        with self.assertRaisesRegex(ValidationError, "greater than zero"):
            OrderRequest.from_values("BTCUSDT", "BUY", "MARKET", "0")


class OrderServiceTests(unittest.TestCase):
    def test_places_order_and_parses_response(self):
        client = FakeClient(
            {
                "orderId": 123,
                "status": "FILLED",
                "executedQty": "0.01",
                "avgPrice": "105432.10",
            }
        )
        service = OrderService(client, logging.getLogger("test"))

        result = service.place_order(
            OrderRequest.from_values("BTCUSDT", "BUY", "MARKET", "0.01")
        )

        self.assertEqual(client.params["symbol"], "BTCUSDT")
        self.assertEqual(result.order_id, "123")
        self.assertEqual(result.average_price, "105432.10")

    def test_zero_average_price_is_displayed_as_na(self):
        client = FakeClient({"orderId": 456, "status": "NEW", "avgPrice": "0"})
        result = OrderService(client, logging.getLogger("test")).place_order(
            OrderRequest.from_values("BTCUSDT", "SELL", "LIMIT", "0.01", "120000")
        )

        self.assertEqual(result.average_price, "N/A")


if __name__ == "__main__":
    unittest.main()

