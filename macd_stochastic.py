import MetaTrader5 as mt5
import pandas as pd

def calculate_macd(df, fast_period=12, slow_period=26, signal_period=9):
    df['EMA_fast'] = df['close'].ewm(span=fast_period, adjust=False).mean()
    df['EMA_slow'] = df['close'].ewm(span=slow_period, adjust=False).mean()
    df['MACD'] = df['EMA_fast'] - df['EMA_slow']
    df['Signal_line'] = df['MACD'].ewm(span=signal_period, adjust=False).mean()
    return df

def calculate_stochastic_oscillator(df, k_period=14, d_period=3):
    df['L14'] = df['low'].rolling(window=k_period).min()
    df['H14'] = df['high'].rolling(window=k_period).max()
    df['%K'] = 100 * ((df['close'] - df['L14']) / (df['H14'] - df['L14']))
    df['%D'] = df['%K'].rolling(window=d_period).mean()
    return df

def strategy_decision(symbol, timeframe):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
    df = pd.DataFrame(rates)

    df = calculate_macd(df)
    df = calculate_stochastic_oscillator(df)

    last_row = df.iloc[-1]

    macd_crossover = last_row['MACD'] > last_row['Signal_line']
    stochastic_overbought = last_row['%K'] > 80 and last_row['%D'] > 80
    stochastic_oversold = last_row['%K'] < 20 and last_row['%D'] < 20

    if macd_crossover and stochastic_oversold:
        return 'BUY'
    elif not macd_crossover and stochastic_overbought:
        return 'SELL'
    else:
        return 'HOLD'
