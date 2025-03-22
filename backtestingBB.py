import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load CSV data
file_path = "D:/Python Backtest/SOLUSDT3m.csv"
df = pd.read_csv(file_path, parse_dates=[0], index_col=0)

def calculate_indicators(df, length=20, mult=2.0, ema_length=50, rsi_length=14):
    df['SMA'] = df['Close'].rolling(window=length).mean()
    df['STD'] = df['Close'].rolling(window=length).std()
    df['UpperBB'] = df['SMA'] + (mult * df['STD'])
    df['LowerBB'] = df['SMA'] - (mult * df['STD'])
    df['EMA50'] = df['Close'].ewm(span=ema_length, adjust=False).mean()

    # RSI Calculation
    delta = df['Close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = pd.Series(gain).rolling(window=rsi_length, min_periods=1).mean()
    avg_loss = pd.Series(loss).rolling(window=rsi_length, min_periods=1).mean()

    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df

df = calculate_indicators(df)

# Backtesting Variables
initial_balance = 100
balance = initial_balance
position = 0
entry_price = 0
longSL = None  # Stop-loss variable
cumulative_balance = [initial_balance]

buy_signals = []
sell_signals = []

for i in range(1, len(df)):
    touches_lowerBB = df['Low'].iloc[i] <= df['LowerBB'].iloc[i] or df['Low'].iloc[i-1] <= df['LowerBB'].iloc[i-1] 
    price_above_ema = df['Close'].iloc[i] < df['EMA50'].iloc[i] or df['Close'].iloc[i] < df['UpperBB'].iloc[i]

    # Candlestick and Volume Conditions
    green_candle = df['Close'].iloc[i] > df['Open'].iloc[i]
    red_candle_prev = df['Close'].iloc[i-1] < df['Open'].iloc[i-1]
    current_body = abs(df['Close'].iloc[i] - df['Open'].iloc[i])
    prev_body = abs(df['Close'].iloc[i-1] - df['Open'].iloc[i-1])
    body_bigger = current_body > prev_body
    volume_increasing = df['Volume'].iloc[i] > df['Volume'].iloc[i-1]

    # Buy Entry Condition
    if touches_lowerBB and price_above_ema and green_candle and red_candle_prev and body_bigger and volume_increasing and position == 0:
        position = balance / df['Close'].iloc[i]  # Buy with full balance
        entry_price = df['Close'].iloc[i]
        balance = 0
        longSL = df['Low'].iloc[i]  # Stop-loss
        buy_signals.append((df.index[i], df['Close'].iloc[i]))

    # Exit Conditions
    # take_profit_level = df['SMA'].iloc[i]  # Mid BB

    if position > 0:
        if df['Low'].iloc[i] < longSL:  # Stop-loss Hit
            balance = position * longSL
            position = 0
            longSL = None
            sell_signals.append((df.index[i], longSL, 'loss'))
        elif df['Close'].iloc[i] >= df['SMA'].iloc[i]:  # Take-profit
            balance = position * df['Close'].iloc[i]
            position = 0
            longSL = None
            sell_signals.append((df.index[i], df['Close'].iloc[i], 'profit'))

    # Update cumulative balance
    if position > 0:
        cumulative_balance.append(position * df['Close'].iloc[i])
    else:
        cumulative_balance.append(balance)

df['Cumulative Balance'] = cumulative_balance

# Plot Data
fig, axs = plt.subplots(2, 1, figsize=(12, 8))

# Price Chart with Indicators and Buy/Sell Signals
axs[0].plot(df.index, df['Close'], label='Close Price', color='black', alpha=0.7)
axs[0].plot(df.index, df['UpperBB'], label='Upper BB', linestyle='dashed', color='red')
axs[0].plot(df.index, df['LowerBB'], label='Lower BB', linestyle='dashed', color='green')
axs[0].plot(df.index, df['EMA50'], label='50 EMA', color='blue')
axs[0].fill_between(df.index, df['LowerBB'], df['UpperBB'], color='gray', alpha=0.2)

# Plot buy and sell markers
for buy in buy_signals:
    axs[0].scatter(buy[0], buy[1], marker='^', color='green', s=100, label="Buy")
for sell in sell_signals:
    if sell[2] == 'loss':
        axs[0].scatter(sell[0], sell[1], marker='v', color='red', s=100, label="Sell")
    elif sell[2] == 'profit':
        axs[0].scatter(sell[0], sell[1], marker='v', color='blue', s=100, label="Sell")

print(buy_signals)
print(sell_signals)

axs[0].set_title('Bollinger Bands, EMA & Close Price with Buy/Sell Signals')
axs[0].legend()
axs[0].grid()

# Cumulative Balance Chart
axs[1].plot(df.index, df['Cumulative Balance'], label='Cumulative Balance', color='blue')
axs[1].set_title('Cumulative Profit Over Time')
axs[1].legend()
axs[1].grid()

plt.tight_layout()
plt.show()
