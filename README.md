# Binance Futures Testnet Trading Bot

A lightweight Python CLI for placing MARKET and LIMIT orders on the Binance
Futures Testnet (USDT-M).

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Add your Binance Futures Testnet credentials to `.env`. Generate credentials at
[testnet.binancefuture.com](https://testnet.binancefuture.com/).

## Usage

Place a MARKET order:

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

Place a LIMIT order:

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 120000
```

Run without arguments to use interactive prompts:

```bash
python cli.py
```

Activity is logged to `logs/trading_bot.log`. API keys and secrets are never
logged.

## Tests

```bash
python -m unittest discover -s tests -v
```

