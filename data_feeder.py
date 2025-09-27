# In data_feeder.py

import pandas as pd
import yfinance as yf

def get_stock_data(tickers, start_date, end_date):
    """
    Fetches historical closing prices. This version is resilient to individual ticker failures
    and correctly handles data cleaning to prevent warnings and bugs.
    """
    print(f"Attempting to download data for {len(tickers)} tickers...")
    try:
        full_data = yf.download(tickers, start=start_date, end=end_date)
        if full_data.empty:
            return pd.DataFrame()

        close_prices = full_data['Close']
        
        if isinstance(close_prices, pd.Series):
            close_prices = close_prices.to_frame(name=tickers[0])

        # --- DEFINITIVE FIX FOR DATA INTEGRITY ---
        # 1. Create a clean copy to work on, which prevents SettingWithCopyWarning.
        clean_prices = close_prices.copy()

        # 2. Drop columns that are entirely empty (for failed tickers).
        clean_prices.dropna(axis='columns', how='all', inplace=True)
        
        # 3. Drop rows with any remaining NaNs (for holidays, etc.).
        clean_prices.dropna(axis='rows', how='any', inplace=True)
        # --- END OF FIX ---
        
        if clean_prices.empty:
            return pd.DataFrame()

        print(f"Successfully processed data for: {len(clean_prices.columns)} tickers.")
        return clean_prices

    except Exception as e:
        print(f"An unexpected error occurred in get_stock_data: {e}")
        return pd.DataFrame()