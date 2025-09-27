# -*- coding: utf-8 -*-
"""
Created on Thu Sep 18 20:59:58 2025

@author: betha
"""

# In stock_screener.py

import pandas as pd
from data_cacher import get_sp500_price_data # Use the new cacher module

def find_uncorrelated_stocks(current_portfolio_returns, start_date, end_date, top_n=5):
    """
    Finds stocks from the S&P 500 that have the lowest correlation to an existing portfolio,
    using a pre-cached DataFrame of all S&P 500 prices for high performance.
    """
    print("\n--- Screening for hedging opportunities using cached S&P 500 data ---")
    
    if current_portfolio_returns.empty:
        return pd.DataFrame()

    # --- THIS IS THE KEY CHANGE ---
    # Get the entire S&P 500 price data from our new, fast cache.
    universe_data = get_sp500_price_data(start_date, end_date)
    if universe_data.empty:
        print("Could not load S&P 500 price data from cache.")
        return pd.DataFrame()
    # --- END OF CHANGE ---

    universe_returns = universe_data.pct_change()

    combined_returns = pd.concat([universe_returns, current_portfolio_returns.rename('__PORTFOLIO__')], axis=1, join='inner')
    combined_returns.dropna(inplace=True)

    if combined_returns.empty:
        return pd.DataFrame()

    correlation_matrix = combined_returns.corr()
    correlations = correlation_matrix['__PORTFOLIO__'].drop('__PORTFOLIO__', errors='ignore')
    
    corr_df = pd.DataFrame({'Correlation': correlations}).sort_values(by='Correlation', ascending=True)
    
    return corr_df.head(top_n)