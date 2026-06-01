import logging
import unittest

from bot.orders import OrderRequest, OrderService
from bot.validators import ValidationError


class FakeClient:
    def __init__(self, response, refreshed_responses=None):
        self.response = response
        self.params = None
        self.refreshed_responses = list(refreshed_responses or [])
        self.refresh_params = []

    def create_futures_order(self, **params):
        self.params = params
        return self.response

    def get_futures_order(self, **params):
        self.refresh_params.append(params)
        if self.refreshed_responses:
            return self.refreshed_responses.pop(0)
        return self.response


class RefreshFailingClient(FakeClient):
    def get_futures_order(self, **params):
        raise RuntimeError("temporary refresh failure")


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
        self.assertEqual(client.refresh_params, [{"symbol": "BTCUSDT", "orderId": 123}])

    def test_zero_average_price_is_displayed_as_na(self):
        client = FakeClient({"orderId": 456, "status": "NEW", "avgPrice": "0"})
        result = OrderService(client, logging.getLogger("test")).place_order(
            OrderRequest.from_values("BTCUSDT", "SELL", "LIMIT", "0.01", "120000")
        )

        self.assertEqual(result.average_price, "N/A")
        self.assertEqual(client.refresh_params, [])

    def test_market_order_refreshes_new_acknowledgement_until_filled(self):
        client = FakeClient(
            {"orderId": 789, "status": "NEW", "executedQty": "0", "avgPrice": "0"},
            [
                {"orderId": 789, "status": "NEW", "executedQty": "0", "avgPrice": "0"},
                {
                    "orderId": 789,
                    "status": "FILLED",
                    "executedQty": "0.01",
                    "avgPrice": "104500.25",
                },
            ],
        )
        delays = []
        service = OrderService(client, logging.getLogger("test"), sleep=delays.append)

        result = service.place_order(
            OrderRequest.from_values("BTCUSDT", "BUY", "MARKET", "0.01")
        )

        self.assertEqual(result.status, "FILLED")
        self.assertEqual(result.executed_quantity, "0.01")
        self.assertEqual(result.average_price, "104500.25")
        self.assertEqual(len(client.refresh_params), 2)
        self.assertEqual(delays, [0.1])

    def test_market_order_returns_latest_status_after_refresh_attempts(self):
        response = {"orderId": 790, "status": "NEW", "executedQty": "0", "avgPrice": "0"}
        client = FakeClient(response)
        delays = []
        service = OrderService(client, logging.getLogger("test"), sleep=delays.append)

        result = service.place_order(
            OrderRequest.from_values("BTCUSDT", "BUY", "MARKET", "0.01")
        )

        self.assertEqual(result.status, "NEW")
        self.assertEqual(len(client.refresh_params), 3)
        self.assertEqual(delays, [0.1, 0.1])

    def test_market_order_uses_acknowledgement_if_refresh_fails(self):
        response = {"orderId": 791, "status": "NEW", "executedQty": "0", "avgPrice": "0"}
        logger = logging.getLogger("test.refresh_failure")
        service = OrderService(RefreshFailingClient(response), logger)

        with self.assertLogs(logger, level="WARNING") as logs:
            result = service.place_order(
                OrderRequest.from_values("BTCUSDT", "BUY", "MARKET", "0.01")
            )

        self.assertEqual(result.status, "NEW")
        self.assertIn("Unable to refresh MARKET order status", logs.output[0])


if __name__ == "__main__":
    unittest.main()
