# br.py
import pandas as pd

def calculate_bollinger_bands(df, length=30, std_dev=2):
    df['SMA'] = df['close'].rolling(window=length).mean()
    df['STD'] = df['close'].rolling(window=length).std()
    df['Upper_Band'] = df['SMA'] + (df['STD'] * std_dev)
    df['Lower_Band'] = df['SMA'] - (df['STD'] * std_dev)
    return df

def calculate_rsi(df, period=14):
    delta = df['close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def strategy_decision(df):
    df = calculate_bollinger_bands(df)
    df['RSI'] = calculate_rsi(df)

    last_candle = df.iloc[-1]
    if last_candle['RSI'] > 70 and last_candle['close'] > last_candle['Upper_Band']:
        return 'SELL'
    elif last_candle['RSI'] < 30 and last_candle['close'] < last_candle['Lower_Band']:
        return 'BUY'
    else:
        return 'HOLD'
