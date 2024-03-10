import MetaTrader5 as mt5
import pandas as pd

# Calculate RSI
def calculate_rsi(symbol, timeframe, period=14):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period + 100)
    df = pd.DataFrame(rates)
    delta = df['close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

# Calculate OBV
def calculate_obv(df):
    df['daily_return'] = df['close'].diff()
    df['direction'] = df['daily_return'].apply(lambda x: 1 if x > 0 else -1 if x < 0 else 0)
    df['adjusted_volume'] = df['direction'] * df['tick_volume']  # Adjusted to use 'tick_volume'
    df['obv'] = df['adjusted_volume'].cumsum()
    return df['obv'].iloc[-1]

# Simplified strategy decision based on SMA, RSI, OBV
def strategy_decision(symbol, timeframe, pip_threshold=15):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 52 + 100)
    df = pd.DataFrame(rates)

    rsi = calculate_rsi(symbol, timeframe)
    obv = calculate_obv(df)  # Calculate OBV

    # Simplified Moving Averages for Trend Analysis
    df['short_ma'] = df['close'].rolling(window=20).mean()
    df['long_ma'] = df['close'].rolling(window=50).mean()

    # Trend Detection
    trend = None
    if df['short_ma'].iloc[-1] > df['long_ma'].iloc[-1]:
        trend = 'upward'
    elif df['short_ma'].iloc[-1] < df['long_ma'].iloc[-1]:
        trend = 'downward'

    strategies_passed = []
    if rsi < 30:
        strategies_passed.append('RSI < 30')
    if obv > df['obv'].iloc[-2]:
        strategies_passed.append('Increasing OBV')
    if trend == 'upward':
        strategies_passed.append('Upward Trend')
    elif trend == 'downward':
        strategies_passed.append('Downward Trend')

    decision = 'hold'
    if strategies_passed:
        decision = 'buy' if 'Upward Trend' in strategies_passed else 'sell'

    print(f"Symbol: {symbol}, Strategies Passed: {', '.join(strategies_passed) if strategies_passed else 'None'}, Trend: {trend}, Trade Decision: {decision.upper()}")

    return decision
