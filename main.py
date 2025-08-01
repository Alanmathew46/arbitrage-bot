import requests
import time
import threading
import os  # For environment variables

# === CONFIGURATION ===
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("CHAT_ID")
SYMBOLS = ["usdt", "xrp", "bnb"]
THRESHOLD_PERCENT = 0.2
CHECK_INTERVAL = 60  # in seconds

# === EXCHANGE ENDPOINTS ===
ENDPOINTS = {
    "binance": lambda symbol: f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}USDT",
    "coindcx": lambda symbol: f"https://api.coindcx.com/exchange/ticker",
    "wazirx": lambda symbol: f"https://api.wazirx.com/api/v2/tickers/{symbol}usdt"
}

# === FUNCTIONS ===
def get_price_binance(symbol):
    try:
        response = requests.get(ENDPOINTS["binance"](symbol)).json()
        return float(response["price"])
    except Exception:
        return None

def get_price_coindcx(symbol):
    try:
        data = requests.get(ENDPOINTS["coindcx"](symbol)).json()
        pair = f"{symbol.upper()}USDT"
        for item in data:
            if item["market"] == pair:
                return float(item["last_price"])
    except Exception:
        return None

def get_price_wazirx(symbol):
    try:
        response = requests.get(ENDPOINTS["wazirx"](symbol)).json()
        return float(response["last"])
    except Exception:
        return None

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, data=payload)
    except Exception as e:
        print("Failed to send Telegram message:", e)

def check_arbitrage():
    while True:
        for symbol in SYMBOLS:
            prices = {}
            prices["Binance"] = get_price_binance(symbol)
            prices["CoinDCX"] = get_price_coindcx(symbol)
            prices["WazirX"] = get_price_wazirx(symbol)

            valid_prices = {ex: p for ex, p in prices.items() if p is not None}
            if len(valid_prices) < 2:
                continue

            max_ex = max(valid_prices, key=valid_prices.get)
            min_ex = min(valid_prices, key=valid_prices.get)
            max_price = valid_prices[max_ex]
            min_price = valid_prices[min_ex]

            percent_diff = ((max_price - min_price) / min_price) * 100

            if percent_diff >= THRESHOLD_PERCENT:
                profit = round(max_price - min_price, 4)
                message = (
                    f"📊 *Arbitrage Opportunity Detected!*\n"
                    f"Coin: *{symbol.upper()}*\n"
                    f"Buy on: *{min_ex}* at `{min_price}`\n"
                    f"Sell on: *{max_ex}* at `{max_price}`\n"
                    f"💰 Profit: `{profit} USDT` (~{round(percent_diff, 2)}%)"
                )
                send_telegram_message(message)

        time.sleep(CHECK_INTERVAL)

# === RUN BOT ===
threading.Thread(target=check_arbitrage).start()
      
