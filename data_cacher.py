# In data_cacher.py

import pandas as pd
import os
from datetime import date
from ticker_fetcher import get_sp500_tickers
from data_feeder import get_stock_data

def get_sp500_price_data(start_date, end_date):
    """
    Fetches and caches the S&P 500 price data.
    The cache is now date-stamped and considered fresh for the entire day.
    """
    # --- THIS IS THE FIX ---
    # Create a cache file name based on today's date.
    today_str = date.today().strftime('%Y-%m-%d')
    cache_file = f'sp500_prices_{today_str}.csv'
    # --- END OF FIX ---

    if os.path.exists(cache_file):
        print("Loading S&P 500 PRICE DATA from today's cache (fresh).")
        return pd.read_csv(cache_file, index_col='Date', parse_dates=True)

    print(f"--- Creating new price cache for {today_str}. This may take a few minutes... ---")
    try:
        sp500_list = [t['value'] for t in get_sp500_tickers()[0]] # Get just the options list
        
        all_prices = get_stock_data(sp500_list, start_date, end_date)
        
        if all_prices.empty:
            raise ValueError("Download of S&P 500 price data failed.")
            
        all_prices.to_csv(cache_file)
        print(f"--- Price cache '{cache_file}' has been successfully created. ---")
        
        return all_prices

    except Exception as e:
        print(f"An error occurred during S&P 500 price data caching: {e}")
        return pd.DataFrame()