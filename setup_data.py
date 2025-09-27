# -*- coding: utf-8 -*-
"""
Created on Sun Sep 28 00:57:20 2025

@author: betha
"""

# In setup_data.py

import pandas as pd
from datetime import date, timedelta

# We need to import the functions from our backend modules to use them
from ticker_fetcher import get_sp500_tickers
from data_feeder import get_stock_data

def prepare_deployment_data():
    """
    This is a one-time script you run on your local machine.
    Its only job is to download all the necessary data and save it
    as high-performance local cache files that we will commit to GitHub.
    This prevents the live deployed app from timing out on startup.
    """
    print("--- Starting one-time data preparation for deployment ---")

    # --- 1. Prepare Ticker List Cache ---
    print("\nStep 1: Preparing S&P 500 ticker list cache...")
    # This will scrape Wikipedia and create 'sp500_tickers.csv'
    # It also returns the lookup DataFrame which we'll need next.
    _, sp500_lookup_df = get_sp500_tickers()
    print("...Ticker list cache ('sp500_tickers.csv') is ready.")

    # --- 2. Prepare Price Data Cache (as a high-performance Parquet file) ---
    print("\nStep 2: Preparing S&P 500 price data cache...")
    # Define the rolling 2-year date range
    END_DATE = date.today().strftime('%Y-%m-%d')
    START_DATE = (date.today() - timedelta(days=2*365)).strftime('%Y-%m-%d')
    
    # Get the list of tickers from the DataFrame we just created
    sp500_list = sp500_lookup_df['Ticker'].tolist()
    
    # Download all the price data using our resilient data_feeder
    all_prices = get_stock_data(sp500_list, START_DATE, END_DATE)

    if not all_prices.empty:
        # Save it to the fast .parquet format
        price_cache_file = 'sp500_prices.parquet'
        all_prices.to_parquet(price_cache_file)
        print(f"...Price data cache ('{price_cache_file}') is ready.")
    else:
        print("ERROR: Failed to download price data. Aborting.")
        return # Stop the script if data download fails

    print("\n--- Data preparation complete. ---")
    print("You can now commit 'sp500_tickers.csv' and 'sp500_prices.parquet' to your GitHub repository.")
    print("Make sure you have also committed the updated versions of your other .py files.")


if __name__ == '__main__':
    prepare_deployment_data()