import MetaTrader5 as mt5
import time
from datetime import datetime
import pytz
import market_analysis as ma  # Assume this uses the simplified strategy
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
    # Adjust pip threshold based on the currency pair's volatility and market convention
    return 0.0001 if symbol in ["EURUSD", "GBPUSD", "USDJPY"] else 0.01  # Adjusted for crypto and less volatile pairs

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

            volume = 0.1  # Define trade volume
            deviation = 20  # Set max price deviation
            # Fetch the current market price for the symbol
            current_price = mt5.symbol_info_tick(symbol).ask if decision == "BUY" else mt5.symbol_info_tick(symbol).bid



            if decision == "buy":
                tm.place_trade(symbol, "BUY", volume, price=current_price , deviation=deviation)
            elif decision == "sell":
                tm.place_trade(symbol, "SELL", volume, price=current_price ,deviation=deviation)

            # Functions to check daily profit or loss and take action if needed
            tm.check_daily_loss()
            tm.check_daily_profit()

        time.sleep(30)  # Pause the script for 30 seconds before the next cycle

except KeyboardInterrupt:
    print("Script interrupted by user. Closing all trades.")
    for symbol in weekend_symbols + weekday_symbols:
        tm.close_all_trades(symbol)

finally:
    mt5.shutdown()
