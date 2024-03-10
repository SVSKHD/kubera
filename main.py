import MetaTrader5 as mt5
import time
from datetime import datetime
import pytz
import market_analysis as ma  # Ensure this is correctly imported
import trade_management as tm

# Initialize the trading environment
tm.startup_check()

# Trading parameters
timeframe = mt5.TIMEFRAME_M5
ist = pytz.timezone('Asia/Kolkata')

# Define symbol groups
weekend_symbols = ["BTCUSD", "ETHUSD"]
weekday_symbols = ["EURUSD", "GBPUSD", "USDJPY"]

def get_symbols_for_today():
    now_ist = datetime.now(ist)
    day_of_week = now_ist.weekday()
    return weekend_symbols if day_of_week in [5, 6] else weekday_symbols

def adjust_pip_threshold(symbol):
    return 0.0001 if symbol in ["EURUSD", "ETHUSD", "BTCUSD"] else 0.01  # Adjusted for clarity

try:
    while True:
        symbols = get_symbols_for_today()
        for symbol in symbols:
            if symbol not in [s.name for s in mt5.symbols_get()]:
                print(f"Symbol {symbol} not found, skipping.")
                continue

            pip_threshold = adjust_pip_threshold(symbol)
            decision = ma.strategy_decision(symbol, timeframe, pip_threshold=pip_threshold)
            print(f"Strategy decision for {symbol}: {decision}")

            volume = 0.1  # Example volume
            deviation = 20  # Example max price deviation

            if decision == "buy":
                tm.place_trade(symbol, "BUY", volume, deviation=deviation)
            elif decision == "sell":
                tm.place_trade(symbol, "SELL", volume, deviation=deviation)

            tm.check_daily_loss()
            tm.check_daily_profit()

        time.sleep(30)  # Monitor every 5 seconds

except KeyboardInterrupt:
    print("Script interrupted by user. Closing all trades.")
    for symbol in weekend_symbols + weekday_symbols:
        tm.close_all_trades(symbol)

finally:
    mt5.shutdown()
