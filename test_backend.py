# -*- coding: utf-8 -*-
"""
Created on Wed Sep 17 17:47:57 2025

@author: betha
"""

# In test_backend.py

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
print(os.getcwd())
# Import the functions we want to test
from data_feeder import get_stock_data
from risk_calculator import (
    calculate_portfolio_returns,
    calculate_historical_var_es,
    calculate_parametric_var_es,
    calculate_monte_carlo_var_es
)

class TestRiskAnalysisBackend(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Set up data that will be used across multiple tests.
        This method runs once before any tests in the class.
        """
        print("Setting up test data...")
        cls.tickers = ['MSFT', 'GOOGL']
        cls.weights = np.array([0.5, 0.5])
        
        # Use a fixed, recent historical period for consistency
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730) # Approx. 2 years of data
        cls.start_date_str = start_date.strftime('%Y-%m-%d')
        cls.end_date_str = end_date.strftime('%Y-%m-%d')
            
        # Fetch real data once to use in calculations
        cls.price_data = get_stock_data(cls.tickers, cls.start_date_str, cls.end_date_str)

    def test_01_data_fetcher_success(self):
        """
        Test 1: Can we successfully fetch data?
        """
        print("\nRunning test_01_data_fetcher_success...")
        self.assertIsNotNone(self.price_data, "Data fetching should return a DataFrame, not None.")
        self.assertFalse(self.price_data.empty, "Fetched DataFrame should not be empty for valid tickers.")
        # Check if the columns match the requested tickers
        self.assertListEqual(sorted(list(self.price_data.columns)), sorted(self.tickers))
        print("...Success!")

    def test_02_data_fetcher_invalid_ticker(self):
        """
        Test 2: Does the data fetcher handle invalid tickers gracefully?
        """
        print("\nRunning test_02_data_fetcher_invalid_ticker...")
        invalid_data = get_stock_data(['INVALIDTICKERXYZ'], '2023-01-01', '2023-12-31')
        self.assertTrue(invalid_data.empty, "Should return an empty DataFrame for an invalid ticker.")
        print("...Success!")
        
    def test_03_calculate_portfolio_returns(self):
        """
        Test 3: Does the portfolio return calculation work?
        """
        print("\nRunning test_03_calculate_portfolio_returns...")
        # Ensure we have data before proceeding
        self.assertFalse(self.price_data.empty, "Cannot calculate returns, price data is empty.")
        
        portfolio_returns = calculate_portfolio_returns(self.price_data, self.weights)
        self.assertIsInstance(portfolio_returns, pd.Series, "Portfolio returns should be a pandas Series.")
        self.assertFalse(portfolio_returns.empty, "Portfolio returns Series should not be empty.")
        # Check that the number of return entries is one less than the price entries
        self.assertEqual(len(portfolio_returns), len(self.price_data) - 1)
        print("...Success!")

    def test_04_risk_calculations_output(self):
        """
        Test 4: Do all risk calculation functions return valid numbers?
        """
        print("\nRunning test_04_risk_calculations_output...")
        self.assertFalse(self.price_data.empty, "Cannot calculate risk, price data is empty.")
        
        portfolio_returns = calculate_portfolio_returns(self.price_data, self.weights)
        confidence_level = 0.95

        # Historical VaR and ES
        hist_var, hist_es = calculate_historical_var_es(portfolio_returns, confidence_level)
        self.assertIsInstance(hist_var, (int, float), "Historical VaR should be a number.")
        self.assertIsInstance(hist_es, (int, float), "Historical ES should be a number.")
        self.assertGreaterEqual(hist_es, hist_var, "ES should be greater than or equal to VaR.")

        # Parametric VaR and ES
        para_var, para_es = calculate_parametric_var_es(portfolio_returns, confidence_level)
        self.assertIsInstance(para_var, (int, float), "Parametric VaR should be a number.")
        self.assertIsInstance(para_es, (int, float), "Parametric ES should be a number.")
        self.assertGreaterEqual(para_es, para_var, "ES should be greater than or equal to VaR.")

        # Monte Carlo VaR and ES
        mc_var, mc_es = calculate_monte_carlo_var_es(portfolio_returns, confidence_level)
        self.assertIsInstance(mc_var, (int, float), "Monte Carlo VaR should be a number.")
        self.assertIsInstance(mc_es, (int, float), "Monte Carlo ES should be a number.")
        self.assertGreaterEqual(mc_es, mc_var, "ES should be greater than or equal to VaR.")
        print("...Success!")


# This allows you to run the tests by executing the script directly
if __name__ == '__main__':
    unittest.main()