"""
Created on Jul 3, 2014

author: Jev Kuznetsov

License: BSD

Description: Module containing some (technical) indicators
"""

import pandas as pd


def rsi(price, n=14):
    """rsi indicator"""
    gain = price.diff().fillna(
        0
    )  # fifference between day n and n-1, replace nan (first value) with 0

    def rsiCalc(p):
        # subfunction for calculating rsi for one lookback period
        avgGain = p[p > 0].sum() / n
        avgLoss = -p[p < 0].sum() / n
        rs = avgGain / avgLoss
        return 100 - 100 / (1 + rs)

    # run for all periods with rolling_apply
    return pd.rolling_apply(gain, n, rsiCalc)
