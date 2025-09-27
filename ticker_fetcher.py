# In ticker_fetcher.py

import pandas as pd
import os
import time
import requests

def get_sp500_tickers():
    """
    Fetches the list of S&P 500 stocks, using a local cache.
    Returns both dropdown options and a clean lookup DataFrame with a 'Ticker' column.
    """
    cache_file = 'sp500_tickers.csv'
    cache_duration_seconds = 24 * 60 * 60

    if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < cache_duration_seconds:
        print("Loading S&P 500 tickers from local cache (fresh).")
        df = pd.read_csv(cache_file)
    else:
        print("Scraping fresh S&P 500 ticker list from Wikipedia...")
        try:
            wiki_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
            response = requests.get(wiki_url, headers=headers)
            response.raise_for_status()
            from io import StringIO
            sp500_table = pd.read_html(StringIO(response.text))[0]
            df = sp500_table[['Symbol', 'Security']]
            df['Symbol'] = df['Symbol'].str.replace('.', '-', regex=False)
            df.to_csv(cache_file, index=False)
            print(f"Successfully scraped and cached {len(df)} S&P 500 tickers.")
        except Exception as e:
            print(f"An error occurred while scraping S&P 500 tickers: {e}")
            df = pd.DataFrame([
                {'Symbol': 'AAPL', 'Security': 'Apple Inc.'},
                {'Symbol': 'MSFT', 'Security': 'Microsoft Corporation'},
                {'Symbol': 'GOOGL', 'Security': 'Alphabet Inc.'}
            ])

    # --- THIS IS THE DEFINITIVE FIX ---
    # 1. Create the dropdown options using the original 'Symbol' column.
    options = [{'label': f"{row['Symbol']} - {row['Security']}", 'value': row['Symbol']} for index, row in df.iterrows()]
    
    # 2. Create the lookup DataFrame and immediately rename the columns for consistency.
    lookup_df = df.rename(columns={'Symbol': 'Ticker', 'Security': 'Company Name'})
    # --- END OF FIX ---
    
    return options, lookup_df