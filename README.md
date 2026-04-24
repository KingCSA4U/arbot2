# arbot2

Async triangular arbitrage scanner for MEXC spot markets using `ccxt`.

## What it does

- loads spot markets from MEXC
- generates triangular paths from the configured coin list
- scans for opportunities using ticker bid/ask prices
- logs a dry-run execution decision for the best opportunity found

## Current status

This project is still in scanner and dry-run mode. It does not place real orders.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a `.env` file with:

```env
API_KEY=your_mexc_key
API_SECRET=your_mexc_secret
```

## Run

```powershell
python main.py
```

Press `Ctrl+C` to stop the bot gracefully.

## Notes

- opportunities are estimated from top-of-book ticker data only
- real execution is not implemented yet
- trading logic should be upgraded with slippage, precision, min-notional, and risk controls before going live
