# 🤖 Crypto Alert Bot

A Telegram bot for tracking cryptocurrency prices and managing a personal portfolio.

## Features

- 💰 Real-time price for any coin
- 🚨 Price alerts — get notified when target price is reached
- 📊 Top 10 coins by market cap
- 📈 7-day price chart
- 💼 Personal portfolio tracker

## Commands

| Command | Description |
|--------|-------------|
| `/price bitcoin` | Get current price |
| `/alert bitcoin 50000` | Set price alert |
| `/stop` | Stop all alerts |
| `/top` | Top 10 coins |
| `/chart bitcoin` | 7-day price chart |
| `/portfolio` | View portfolio |
| `/portfolio add bitcoin 0.5` | Add coin to portfolio |
| `/portfolio remove bitcoin` | Remove coin |

## Setup

1. Clone the repository
2. Install dependencies: `pip install pytelegrambotapi requests matplotlib`
3. Add your bot token: replace `YOUR_BOT_TOKEN_HERE` in `Bot.py`
4. Run: `python Bot.py`

## Built With

- Python
- pyTelegramBotAPI
- CoinGecko API
- Matplotlib
