# app.py
# Alpaca Paper Trading Trend-Following Bot (IB Style)

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import os


# -----------------------------
# Binary Search Tree Node
# -----------------------------
class Node:
    def __init__(self, score, symbol):
        self.score = score
        self.symbol = symbol
        self.left = None
        self.right = None


def insert(node, score, symbol):
    if node is None:
        return Node(score, symbol)

    if score < node.score:
        node.left = insert(node.left, score, symbol)
    else:
        node.right = insert(node.right, score, symbol)

    return node


def traverse_descending(node, ranked):
    if node is None:
        return
    traverse_descending(node.right, ranked)
    ranked.append((node.symbol, node.score))
    traverse_descending(node.left, ranked)


# -----------------------------
# Moving Average
# -----------------------------
def moving_average(prices, period):
    return sum(prices[-period:]) / period


# -----------------------------
# MAIN PROGRAM
# -----------------------------
def main():

    # Alpaca clients (PAPER TRADING)
    trading_client = TradingClient(
        os.getenv("APCA_API_KEY_ID"),
        os.getenv("APCA_API_SECRET_KEY"),
        paper=True
    )

    data_client = StockHistoricalDataClient(
        os.getenv("APCA_API_KEY_ID"),
        os.getenv("APCA_API_SECRET_KEY")
    )

    watchlist = [
        "AAPL", "MSFT", "GOOG", "AMZN", "TSLA",
        "NVDA", "META", "NFLX", "BABA", "ADBE"
    ]

    root = None
    ma_cache = {}

    # -----------------------------
    # DATA RETRIEVAL
    # -----------------------------
    for symbol in watchlist:
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            limit=210
        )

        bars = data_client.get_stock_bars(request).data[symbol]
        closes = [bar.close for bar in bars]

        if len(closes) < 200:
            continue

        short_ma = moving_average(closes, 50)
        long_ma = moving_average(closes, 200)

        prev_short = moving_average(closes[:-1], 50)
        prev_long = moving_average(closes[:-1], 200)

        trend_score = round(short_ma - long_ma, 2)
        ma_cache[symbol] = (short_ma, long_ma, prev_short, prev_long)

        root = insert(root, trend_score, symbol)

    # -----------------------------
    # RANK STOCKS (BST)
    # -----------------------------
    ranked = []
    traverse_descending(root, ranked)

    print("\n--- Ranked Stocks ---")

    for symbol, score in ranked:
        short_ma, long_ma, prev_short, prev_long = ma_cache[symbol]

        # BUY: Golden Cross
        if prev_short <= prev_long and short_ma > long_ma:
            print(f"{symbol}: BUY")

            order = MarketOrderRequest(
                symbol=symbol,
                qty=10,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )

            trading_client.submit_order(order)

        # SELL: Death Cross
        elif prev_short >= prev_long and short_ma < long_ma:
            print(f"{symbol}: SELL")

            order = MarketOrderRequest(
                symbol=symbol,
                qty=10,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )

            trading_client.submit_order(order)

        else:
            print(f"{symbol}: HOLD")

    print("\nRun complete (paper trading).")


if __name__ == "__main__":
    main()


