# -*- coding: utf-8 -*-
"""
Created on Wed Sep 17 17:43:11 2025

@author: betha
"""

# In risk_calculator.py
'''
it is a good project, i like this 
is there any possibility that we add a new moodule ? 
i am thinking of suggesting a stock to my "client" that minimizes his risk. Like, "minimazing" its Var 
he gives me this: 
Budget (we should change the weight with pieces of stocks) , minimum expected 
'''
import pandas as pd
import numpy as np
from scipy.stats import norm

def calculate_portfolio_returns(price_data, weights):
    """
    Calculates the daily returns of a portfolio.

    Args:
        price_data (pd.DataFrame): DataFrame of adjusted closing prices.
        weights (np.array): Array of weights for each asset in the portfolio.

    Returns:
        pd.Series: A Series of daily portfolio returns.
    """
    # Calculate daily percentage returns for each stock
    daily_returns = price_data.pct_change().dropna()
    
    # Calculate the weighted returns for the portfolio
    portfolio_returns = daily_returns.dot(weights)
    
    return portfolio_returns

def calculate_historical_var_es(returns, confidence_level=0.95):
    """
    Calculates Value at Risk (VaR) and Expected Shortfall (ES) using historical simulation.

    Args:
        returns (pd.Series): A Series of portfolio returns.
        confidence_level (float): The confidence level (e.g., 0.95 for 95%).

    Returns:
        tuple: A tuple containing the VaR and ES, expressed as positive percentages.
    """
    # VaR is the percentile of the historical returns
    var = -np.percentile(returns, (1 - confidence_level) * 100)
    
    # ES is the average of the returns that are worse than the VaR
    es = -returns[returns < -var].mean()
    
    return var, es

def calculate_parametric_var_es(returns, confidence_level=0.95):
    """
    Calculates VaR and ES using the parametric (variance-covariance) method.

    Args:
        returns (pd.Series): A Series of portfolio returns.
        confidence_level (float): The confidence level.

    Returns:
        tuple: A tuple containing the VaR and ES, expressed as positive percentages.
    """
    # Calculate the mean and standard deviation of returns
    mu = np.mean(returns)
    sigma = np.std(returns)
    
    # Calculate VaR using the inverse of the normal distribution's CDF (Z-score)
    var = -(mu + sigma * norm.ppf(1 - confidence_level))
    
    # Calculate ES for a normal distribution
    es = -(mu - sigma * (norm.pdf(norm.ppf(1 - confidence_level)) / (1 - confidence_level)))

    return var, es

def calculate_monte_carlo_var_es(returns, confidence_level=0.95, simulations=10000, days_to_simulate=1):
    """
    Calculates VaR and ES using Monte Carlo simulation.

    Args:
        returns (pd.Series): A Series of portfolio returns.
        confidence_level (float): The confidence level.
        simulations (int): The number of simulations to run.
        days_to_simulate (int): The number of days into the future to simulate (typically 1 for daily VaR).

    Returns:
        tuple: A tuple containing the VaR and ES, expressed as positive percentages.
    """
    mu = np.mean(returns)
    sigma = np.std(returns)

    # Generate random simulations based on the normal distribution
    simulated_returns = np.random.normal(mu, sigma, (simulations, days_to_simulate))
    
    # For 1-day VaR, we just look at the simulated returns for that day
    final_returns = simulated_returns[:, 0]

    # Calculate VaR and ES from the simulated distribution (using the historical method on simulated data)
    var = -np.percentile(final_returns, (1 - confidence_level) * 100)
    es = -final_returns[final_returns < -var].mean()
    
    return var, es
# In main.py
# (keep all the existing imports and functions)

# --- NEW IMPORTS ---
#from portfolio_optimizer import find_minimum_volatility_portfolio, calculate_shares_from_budget

# ... (keep the existing plot_analysis, analyze_and_display_correlation, and run_risk_analysis functions) ...

# --- NEW FUNCTION ---
def run_portfolio_optimization(candidate_tickers, budget, start_date, end_date):
    """
    Orchestrates the entire portfolio optimization process.
    """
    print(f"\n>>> Running Portfolio Optimization for: {', '.join(candidate_tickers)}")
    
    # 1. Fetch data for candidate stocks
    price_data = get_stock_data(candidate_tickers, start_date, end_date)
    if price_data.empty:
        print("--- OPTIMIZATION HALTED: Could not fetch data. ---")
        return

    # 2. Calculate necessary inputs for the optimizer
    returns = price_data.pct_change().dropna()
    mean_returns = returns.mean()
    cov_matrix = returns.cov()

    # 3. Find the optimal weights that minimize volatility
    print("\n--- Finding Optimal Portfolio Weights ---")
    optimal_weights = find_minimum_volatility_portfolio(mean_returns, cov_matrix)
    print("Optimal weights found for minimum risk.")

    # 4. Run our original VaR analysis on this NEW optimized portfolio
    print("\n--- Analyzing Risk of the Optimized Portfolio ---")
    run_risk_analysis(candidate_tickers, optimal_weights, start_date, end_date, CONFIDENCE_LEVEL)

    # 5. Calculate the number of shares to buy based on the budget
    latest_prices = price_data.iloc[-1] # Get the most recent prices
    calculate_shares_from_budget(candidate_tickers, optimal_weights, budget, latest_prices)


# ==============================================================================
# --- YOUR EXPERIMENTATION AREA ---
# ==============================================================================
if __name__ == "__main__":
    
    START_DATE = '2021-01-01'
    END_DATE = '2023-12-31'
    CONFIDENCE_LEVEL = 0.99
    
    # --- New Optimization Scenario ---
    # The "client" is considering these stocks and has a budget of $25,000.
    # What is the safest way to invest it?
    
    CLIENT_BUDGET = 25000
    CANDIDATE_TICKERS = ['AAPL', 'MSFT', 'JNJ', 'JPM', 'XOM'] # A mix of Tech, Health, Finance, Energy
    
    run_portfolio_optimization(CANDIDATE_TICKERS, CLIENT_BUDGET, START_DATE, END_DATE)