# In stock_screener.py

import pandas as pd
from data_cacher import get_sp500_price_data

def find_uncorrelated_stocks(current_portfolio_returns, top_n=5):
    """
    Finds S&P 500 stocks with the lowest correlation to a portfolio, using the cache.
    """
    print("\n--- Screening for hedging opportunities using cached S&P 500 data ---")
    
    if current_portfolio_returns.empty:
        return pd.DataFrame()

    universe_data = get_sp500_price_data()
    if universe_data.empty:
        print("Could not load S&P 500 price data from cache.")
        return pd.DataFrame()

    universe_returns = universe_data.pct_change()

    combined_returns = pd.concat([universe_returns, current_portfolio_returns.rename('__PORTFOLIO__')], axis=1, join='inner')
    combined_returns.dropna(inplace=True)

    if combined_returns.empty:
        return pd.DataFrame()

    correlation_matrix = combined_returns.corr()
    if '__PORTFOLIO__' not in correlation_matrix:
        return pd.DataFrame()
        
    correlations = correlation_matrix['__PORTFOLIO__'].drop('__PORTFOLIO__', errors='ignore')
    
    corr_df = pd.DataFrame({'Correlation': correlations}).sort_values(by='Correlation', ascending=True)
    
    return corr_df.head(top_n)