# -*- coding: utf-8 -*-
"""
Created on Thu Sep 18 20:59:58 2025

@author: betha
"""

# In stock_screener.py

import pandas as pd
from data_cacher import get_sp500_price_data # Use the cacher

def find_uncorrelated_stocks(current_portfolio_returns, start_date, end_date, top_n=5):
    """
    Finds S&P 500 stocks with the lowest correlation to a portfolio.
    This version is highly robust and designed to never crash on a server.
    """
    print("\n--- Screening for hedging opportunities using cached data ---")
    
    if current_portfolio_returns.empty:
        print("LOG: Current portfolio returns are empty. Cannot find suggestions.")
        return pd.DataFrame()

    # --- 1. Load the universe price data safely ---
    try:
        universe_data = get_sp500_price_data()
        if universe_data.empty:
            print("LOG: Cached S&P 500 price data is empty.")
            return pd.DataFrame()
    except FileNotFoundError:
        print("CRITICAL ERROR: The cache file 'sp500_prices.parquet' was not found on the server.")
        return pd.DataFrame()
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to load price cache. Error: {e}")
        return pd.DataFrame()

    universe_returns = universe_data.pct_change()

    # --- 2. Robustly combine the data ---
    # This ensures that we only try to find correlations for stocks that
    # actually exist in our cached price data.
    
    # Find the common tickers between the universe and the user's portfolio
    portfolio_tickers = current_portfolio_returns.name
    # This check is not needed if current_portfolio_returns is a Series, let's simplify
    
    # The most robust way to combine is to align them.
    # This will handle any date mismatches perfectly.
    aligned_universe, aligned_portfolio = universe_returns.align(current_portfolio_returns, join='inner', axis=0)

    if aligned_universe.empty or aligned_portfolio.empty:
        print("LOG: No overlapping trading days found. Cannot calculate correlation.")
        return pd.DataFrame()

    # --- 3. Calculate correlations safely ---
    # We add the portfolio as a temporary column to calculate all correlations at once.
    aligned_universe['__PORTFOLIO__'] = aligned_portfolio
    
    try:
        correlation_matrix = aligned_universe.corr()
        if '__PORTFOLIO__' not in correlation_matrix:
            print("LOG: Could not calculate correlation matrix correctly.")
            return pd.DataFrame()
            
        correlations = correlation_matrix['__PORTFOLIO__'].drop('__PORTFOLIO__', errors='ignore')
    except Exception as e:
        print(f"CRITICAL ERROR: Correlation calculation failed. Error: {e}")
        return pd.DataFrame()
    
    corr_df = pd.DataFrame({'Correlation': correlations}).sort_values(by='Correlation', ascending=True)
    
    return corr_df.head(top_n)