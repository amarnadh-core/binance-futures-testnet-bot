"""Command-line interface for the Binance Futures Testnet trading bot."""

import argparse
import logging
from typing import Sequence

from bot.client import BinanceClientError, BinanceTradingClient
from bot.config import ConfigurationError, Settings
from bot.logging_config import configure_logging
from bot.orders import OrderRequest, OrderResult, OrderService
from bot.validators import ValidationError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Place MARKET and LIMIT orders on Binance Futures Testnet."
    )
    parser.add_argument("--symbol", help="Trading pair, for example BTCUSDT")
    parser.add_argument("--side", help="Order side: BUY or SELL")
    parser.add_argument("--type", dest="order_type", help="Order type: MARKET or LIMIT")
    parser.add_argument("--quantity", help="Order quantity, greater than zero")
    parser.add_argument("--price", help="LIMIT order price, greater than zero")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logger = configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        values = _collect_values(args)
        order = OrderRequest.from_values(**values)
        _print_summary(order)
        settings = Settings.from_env()
        service = OrderService(
            BinanceTradingClient(settings.api_key, settings.api_secret),
            logger,
        )
        result = service.place_order(order)
        _print_result(result)
        return 0
    except (ValidationError, ConfigurationError, BinanceClientError) as exc:
        logger.error("%s", exc)
        print(f"\nError: {exc}")
        return 1
    except (EOFError, KeyboardInterrupt):
        logger.warning("Input cancelled by user")
        print("\nCancelled.")
        return 130


def _collect_values(args: argparse.Namespace) -> dict[str, str | None]:
    interactive = not any(
        [args.symbol, args.side, args.order_type, args.quantity, args.price]
    )
    if interactive:
        symbol = input("Enter Symbol: ")
        side = input("Enter Side (BUY/SELL): ")
        order_type = input("Enter Order Type (MARKET/LIMIT): ")
        return {
            "symbol": symbol,
            "side": side,
            "order_type": order_type,
            "quantity": input("Enter Quantity: "),
            "price": input("Enter Price: ") if order_type.strip().upper() == "LIMIT" else None,
        }

    return {
        "symbol": args.symbol or "",
        "side": args.side or "",
        "order_type": args.order_type or "",
        "quantity": args.quantity or "",
        "price": args.price,
    }


def _print_summary(order: OrderRequest) -> None:
    print("\n" + "=" * 50)
    print("ORDER REQUEST SUMMARY")
    print("=" * 50)
    print(f"Symbol   : {order.symbol}")
    print(f"Side     : {order.side}")
    print(f"Type     : {order.order_type}")
    print(f"Quantity : {order.quantity}")
    if order.price is not None:
        print(f"Price    : {order.price}")
    print("=" * 50)


def _print_result(result: OrderResult) -> None:
    print("\nOrder placed successfully\n")
    print(f"Order ID     : {result.order_id}")
    print(f"Status       : {result.status}")
    print(f"Executed Qty : {result.executed_quantity}")
    print(f"Avg Price    : {result.average_price}")


if __name__ == "__main__":
    raise SystemExit(main())
