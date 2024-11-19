import numpy as np

def calculate_rsi(prices, period=14):
    deltas = np.diff(prices)
    gains = np.maximum(deltas, 0)
    losses = np.abs(np.minimum(deltas, 0))

    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    for i in range(period, len(prices) - 1):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    rs = avg_gain / (avg_loss + avg_gain)
    return rs * 100

def calculate_bollinger_bands(prices, period=20, num_std_dev=2):
    middle_band = np.mean(prices[-period:])
    std_dev = np.std(prices[-period:])
    upper_band = middle_band + (num_std_dev * std_dev)
    lower_band = middle_band - (num_std_dev * std_dev)
    return middle_band, upper_band, lower_band