# In ticker_fetcher.py
import pandas as pd
import requests

def fetch_sp500_df():
    """
    Scrapes Wikipedia for the list of S&P 500 companies.
    This is ONLY for the setup script.
    """
    print("Scraping fresh S&P 500 ticker list from Wikipedia...")
    try:
        wiki_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(wiki_url, headers=headers)
        response.raise_for_status()
        from io import StringIO
        sp500_table = pd.read_html(StringIO(response.text))[0]
        df = sp500_table[['Symbol', 'Security']]
        df['Symbol'] = df['Symbol'].str.replace('.', '-', regex=False)
        print(f"Successfully scraped {len(df)} S&P 500 tickers.")
        return df
    except Exception as e:
        print(f"An error occurred while scraping S&P 500 tickers: {e}")
        return pd.DataFrame([{'Symbol': 'AAPL', 'Security': 'Apple Inc.'}])