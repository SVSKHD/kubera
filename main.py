import MetaTrader5 as mt5
import trade_management as tm
import time
from datetime import datetime
import pytz
import br  # Bollinger Bands + RSI strategy
import macd_stoch_strategy  # MACD + Stochastic Oscillator strategy

tm.startup_check()
timeframe = mt5.TIMEFRAME_M15
ist = pytz.timezone('Asia/Kolkata')

weekend_symbols = ["BTCUSD", "ETHUSD"]
weekday_symbols = ["EURUSD", "GBPUSD", "USDJPY"]

def get_symbols_for_today():
    now_ist = datetime.now(ist)
    return weekend_symbols if now_ist.weekday() in [5, 6] else weekday_symbols

def adjust_pip_threshold(symbol):
    return 0.01 if symbol == "USDJPY" else 0.0001

try:
    while True:
        symbols = get_symbols_for_today()
        for symbol in symbols:
            if symbol not in [s.name for s in mt5.symbols_get()]:
                print(f"Symbol {symbol} not found, skipping.")
                continue

            pip_threshold = adjust_pip_threshold(symbol)
            
            # Fetch market data
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
            df = pd.DataFrame(rates)

            # Get decisions from both strategies
            br_decision = br.strategy_decision(symbol, timeframe)
            macd_stoch_decision = macd_stoch_strategy.strategy_decision(df)

            # Combining decisions for a more robust trading signal
            final_decision = 'HOLD'  # Default decision
            if br_decision == 'BUY' and macd_stoch_decision == 'BUY':
                final_decision = 'BUY'
            elif br_decision == 'SELL' and macd_stoch_decision == 'SELL':
                final_decision = 'SELL'

            print(f"Final decision for {symbol}: {final_decision}")
            
            # Trade execution based on final_decision
            if final_decision in ["BUY", "SELL"]:
                volume = 0.1
                deviation = 20
                tm.place_trade(symbol, final_decision, volume, price=0, deviation)

            tm.check_daily_loss()
            tm.check_daily_profit()

        time.sleep(30)

except KeyboardInterrupt:
    print("Script interrupted by user. Shutting down.")
    for symbol in weekend_symbols + weekday_symbols:
        tm.close_all_trades(symbol)

finally:
    mt5.shutdown()
