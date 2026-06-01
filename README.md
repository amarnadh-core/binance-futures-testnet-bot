# Binance Futures Testnet Trading Bot

A lightweight Python CLI application for placing **MARKET** and **LIMIT**
orders on the **Binance Futures Testnet (USDT-M)**.

The project demonstrates clean architecture, input validation, structured
logging, error handling, and automated tests.

## Features

- Place MARKET and LIMIT orders
- Support BUY and SELL sides
- Use command-line arguments or interactive prompts
- Validate input with clear error messages
- Log order activity and API responses to a file
- Handle Binance API errors
- Ensure orders are routed only to Binance Futures Testnet
- Run automated unit tests without sending real API requests

## Setup

### Create and activate a virtual environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux or macOS:

```bash
source venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure API credentials

Create a `.env` file from the provided template.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Windows Command Prompt:

```bat
copy .env.example .env
```

Linux or macOS:

```bash
cp .env.example .env
```

Update `.env` with your Binance Futures Testnet credentials:

```env
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
```

Generate credentials at
[testnet.binancefuture.com](https://testnet.binancefuture.com/).

## Usage

### Place a MARKET order

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Place a LIMIT order

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 120000
```

### Interactive mode

Run without arguments:

```bash
python cli.py
```

Example:

```text
Enter Symbol: BTCUSDT
Enter Side (BUY/SELL): BUY
Enter Order Type (MARKET/LIMIT): LIMIT
Enter Quantity: 0.01
Enter Price: 120000
```

## Example Output

```text
==================================================
ORDER REQUEST SUMMARY
==================================================
Symbol   : BTCUSDT
Side     : BUY
Type     : MARKET
Quantity : 0.01
==================================================

Order placed successfully

Order ID     : 123456789
Status       : NEW
Executed Qty : 0.0000
Avg Price    : N/A
```

## Logging

Application activity is written to:

```text
logs/trading_bot.log
```

The log file includes order requests, Binance API responses, validation errors,
and Binance API errors. API keys and secrets are never logged.

## Project Structure

```text
trading_bot/
|-- bot/
|   |-- __init__.py
|   |-- client.py
|   |-- config.py
|   |-- logging_config.py
|   |-- orders.py
|   `-- validators.py
|-- logs/
|-- tests/
|   |-- test_client.py
|   `-- test_orders.py
|-- .env.example
|-- .gitignore
|-- cli.py
|-- requirements.txt
`-- README.md
```

## Running Tests

Execute the test suite:

```bash
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

## Notes

- All orders are placed on the Binance Futures Testnet.
- The client verifies that Futures requests resolve to
  `https://testnet.binancefuture.com/fapi` before allowing an order.
- LIMIT orders use `GTC` (Good Till Cancelled).
- Input is validated before requests are submitted.
- Binance exchange rules, such as minimum quantity and price filters, are
  enforced by the exchange and returned as user-facing API errors.
