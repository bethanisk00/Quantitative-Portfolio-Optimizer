# In portfolio_optimizer.py

import numpy as np
import pandas as pd
from scipy.optimize import minimize

def calculate_portfolio_performance(weights, mean_returns, cov_matrix):
    """Calculates the annualized return and volatility for a given set of weights."""
    weights = np.array(weights)
    returns = np.sum(mean_returns * weights) * 252
    std_dev = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(252)
    return returns, std_dev

def get_final_allocation(mean_returns, cov_matrix, target_profile, risk_free_rate, 
                         current_weights, max_allocation, sell_enabled):
    """
    Determines the final optimal weights with a robust, multi-profile strategy
    and a final cleaning step to remove numerical noise.
    """
    num_assets = len(mean_returns)
    initial_weights = np.array(num_assets * [1. / num_assets,])

    # --- Define Objective Functions ---
    def portfolio_volatility(weights):
        return calculate_portfolio_performance(weights, mean_returns, cov_matrix)[1]

    def risk_contribution_objective(weights):
        weights = np.array(weights)
        portfolio_vol = portfolio_volatility(weights)
        if portfolio_vol == 0: return 0
        marginal_contribution = cov_matrix.dot(weights)
        risk_contribution = weights * marginal_contribution / portfolio_vol
        return np.std(risk_contribution)

    def negative_portfolio_return(weights):
        return -calculate_portfolio_performance(weights, mean_returns, cov_matrix)[0]

    # --- Define Constraints and Bounds ---
    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
    bounds = tuple((0, max_allocation) for _ in range(num_assets))

    if not sell_enabled and current_weights is not None:
        print("Constraint Applied: Selling is disabled.")
        for i in range(num_assets):
            constraints.append({'type': 'ineq', 'fun': lambda w, i=i: w[i] - current_weights[i]})

    # --- Intelligent Profile Switching ---
    avg_expected_return = calculate_portfolio_performance(initial_weights, mean_returns, cov_matrix)[0]
    if target_profile == 'balanced' and avg_expected_return < risk_free_rate:
        print("\nWARNING: Expected returns are low/negative. Switching 'Balanced' to 'Minimum Risk'.")
        target_profile = 'min_risk'

    # --- Select Objective and Run Optimizer ---
    if target_profile == 'min_risk':
        print("Optimizing for: Minimum Risk")
        result = minimize(portfolio_volatility, initial_weights, method='SLSQP', bounds=bounds, constraints=constraints)
    
    elif target_profile == 'balanced':
        print("Optimizing for: Balanced (Risk Parity)")
        result = minimize(risk_contribution_objective, initial_weights, method='SLSQP', bounds=bounds, constraints=constraints)
        
    elif target_profile == 'high_growth':
        print("Optimizing for: High Growth (Return Targeting)")
        individual_returns = mean_returns * 252
        target_return = np.percentile(individual_returns, 75)
        print(f"Setting a target annualized return of {target_return:.2%}")
        growth_constraints = constraints + [{'type': 'eq', 'fun': lambda w: calculate_portfolio_performance(w, mean_returns, cov_matrix)[0] - target_return}]
        result = minimize(portfolio_volatility, initial_weights, method='SLSQP', bounds=bounds, constraints=growth_constraints)

    else:
        # Fallback to Minimum Risk if profile is unknown
        result = minimize(portfolio_volatility, initial_weights, method='SLSQP', bounds=bounds, constraints=constraints)

    # --- Final Fallback ---
    if not result.success:
        print("\nCRITICAL WARNING: Optimization failed. Re-running with a simple Minimum Risk objective.")
        fallback_constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
        fallback_result = minimize(portfolio_volatility, initial_weights, method='SLSQP', bounds=bounds, constraints=fallback_constraints)
        
        if not fallback_result.success:
            print("ULTIMATE FALLBACK: Returning an equal-weight portfolio.")
            return initial_weights
        
        optimal_weights = fallback_result.x
    else:
        optimal_weights = result.x

    # --- DEFINITIVE FIX: Weight Cleaning ---
    # 1. Set any weights that are extremely close to zero to be exactly 0.
    optimal_weights[np.isclose(optimal_weights, 0)] = 0
    
    # 2. Re-normalize the weights to ensure they sum perfectly to 1 after cleaning.
    if np.sum(optimal_weights) > 0:
        optimal_weights /= np.sum(optimal_weights)
    # --- END OF FIX ---

    return optimal_weights