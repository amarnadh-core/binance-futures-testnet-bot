"""Order construction, submission, and response parsing."""

from dataclasses import dataclass
from decimal import Decimal
import logging
import time
from typing import Any, Callable, Protocol

from .validators import (
    validate_order_type,
    validate_positive_decimal,
    validate_side,
    validate_symbol,
)


class FuturesOrderClient(Protocol):
    def create_futures_order(self, **params: Any) -> dict[str, Any]: ...

    def get_futures_order(self, **params: Any) -> dict[str, Any]: ...


@dataclass(frozen=True)
class OrderRequest:
    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Decimal | None = None

    @classmethod
    def from_values(
        cls,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str | Decimal,
        price: str | Decimal | None = None,
    ) -> "OrderRequest":
        normalized_type = validate_order_type(order_type)
        normalized_price = None
        if normalized_type == "LIMIT":
            if price is None or str(price).strip() == "":
                from .validators import ValidationError

                raise ValidationError("Price is required for LIMIT orders.")
            normalized_price = validate_positive_decimal("Price", price)

        return cls(
            symbol=validate_symbol(symbol),
            side=validate_side(side),
            order_type=normalized_type,
            quantity=validate_positive_decimal("Quantity", quantity),
            price=normalized_price,
        )

    def to_api_params(self) -> dict[str, str]:
        params = {
            "symbol": self.symbol,
            "side": self.side,
            "type": self.order_type,
            "quantity": _decimal_text(self.quantity),
        }
        if self.order_type == "LIMIT":
            params["timeInForce"] = "GTC"
            params["price"] = _decimal_text(self.price)
        return params


@dataclass(frozen=True)
class OrderResult:
    order_id: str
    status: str
    executed_quantity: str
    average_price: str

    @classmethod
    def from_response(cls, response: dict[str, Any]) -> "OrderResult":
        average_price = str(response.get("avgPrice", "0"))
        try:
            if Decimal(average_price) <= 0:
                average_price = "N/A"
        except Exception:
            average_price = "N/A"

        return cls(
            order_id=str(response.get("orderId", "N/A")),
            status=str(response.get("status", "UNKNOWN")),
            executed_quantity=str(response.get("executedQty", "0")),
            average_price=average_price,
        )


class OrderService:
    _TERMINAL_STATUSES = {"FILLED", "CANCELED", "EXPIRED", "REJECTED"}

    def __init__(
        self,
        client: FuturesOrderClient,
        logger: logging.Logger,
        market_refresh_attempts: int = 3,
        market_refresh_delay: float = 0.1,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client = client
        self._logger = logger
        self._market_refresh_attempts = market_refresh_attempts
        self._market_refresh_delay = market_refresh_delay
        self._sleep = sleep

    def place_order(self, order: OrderRequest) -> OrderResult:
        params = order.to_api_params()
        self._logger.info(
            "Request: %s %s %s qty=%s",
            order.order_type,
            order.side,
            order.symbol,
            params["quantity"],
        )
        response = self._client.create_futures_order(**params)
        self._logger.info("Response: %s", response)
        if order.order_type == "MARKET":
            response = self._refresh_market_order(order.symbol, response)
        result = OrderResult.from_response(response)
        self._logger.info("Order completed successfully: orderId=%s", result.order_id)
        return result

    def _refresh_market_order(
        self, symbol: str, initial_response: dict[str, Any]
    ) -> dict[str, Any]:
        order_id = initial_response.get("orderId")
        if order_id is None:
            self._logger.warning("MARKET order response did not include an orderId")
            return initial_response

        latest_response = initial_response
        for attempt in range(self._market_refresh_attempts):
            if attempt:
                self._sleep(self._market_refresh_delay)
            try:
                latest_response = self._client.get_futures_order(
                    symbol=symbol, orderId=order_id
                )
            except Exception as exc:
                self._logger.warning(
                    "Unable to refresh MARKET order status for orderId=%s: %s",
                    order_id,
                    exc,
                )
                return latest_response

            self._logger.info(
                "MARKET order status refresh %s/%s: %s",
                attempt + 1,
                self._market_refresh_attempts,
                latest_response,
            )
            if str(latest_response.get("status", "")).upper() in self._TERMINAL_STATUSES:
                break

        return latest_response


def _decimal_text(value: Decimal | None) -> str:
    if value is None:
        return ""
    return format(value, "f")
