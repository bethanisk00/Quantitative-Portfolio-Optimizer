# In data_cacher.py

import pandas as pd
import os

def get_sp500_price_data():
    """
    Loads the pre-compiled S&P 500 price data from the local Parquet cache.
    """
    cache_file = 'sp500_prices.parquet'
    if not os.path.exists(cache_file):
        print(f"CRITICAL ERROR: Cache file '{cache_file}' not found.")
        return pd.DataFrame()
    
    print("Loading S&P 500 PRICE DATA from local cache.")
    return pd.read_parquet(cache_file)