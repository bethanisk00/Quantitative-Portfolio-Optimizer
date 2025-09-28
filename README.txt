# Quantitative Portfolio Optimizer

## Live Demo

**[Click here to access the live application](https://bethanisk.pythonanywhere.com/)

*(Note: The app is hosted on a free/hobbyist tier. The initial load may take up to 60 seconds as the server wakes up. Please be patient!)*

---

## Overview

This project is an interactive web application designed for portfolio risk analysis and optimization. Built with Python and Dash, it allows users to construct a stock portfolio, analyze its current risk profile using key quantitative metrics, and receive mathematically-backed recommendations for rebalancing based on Modern Portfolio Theory (MPT).

The tool helps users answer critical investment questions, such as:
- What is the current risk of my portfolio (Volatility, Value at Risk)?
- What stocks could I add to improve diversification?
- What is the most efficient way to invest new capital based on my personal risk tolerance?

## Key Features

- **Dynamic Portfolio Construction:** Users can build a portfolio by searching for any stock in the S&P 500.
- **Current State Analysis:** Instantly calculates and displays key performance indicators (KPIs) for the user's current holdings:
  - Estimated Annualized Return
  - Annualized Volatility (Risk)
  - Historical Value at Risk (VaR) at 99% confidence.
- **Risk Characterization:** Automatically classifies the current portfolio as "Low", "Moderate", or "High" risk based on its volatility.
- **Hedging Suggestions:** Screens the S&P 500 to find and suggest stocks with the lowest correlation to the user's current portfolio, providing data-driven ideas for diversification.
- **Multi-Profile Optimization:** Offers three distinct, professional-grade optimization strategies:
  - **Minimum Risk:** Finds the portfolio with the absolute lowest possible volatility.
  - **Balanced (Risk Parity):** Creates a portfolio where each asset contributes equally to the overall risk.
  - **High Growth (Return Targeting):** Finds the safest possible portfolio that can achieve a specific, aggressive return target.
- **"No-Sell" Constraint:** Allows users to find the best way to invest new capital *without* selling any of their existing shares.

## Technologies Used

- **Backend:** Python
  - **Data Analysis & Optimization:** Pandas, NumPy, SciPy
  - **Financial Data:** yfinance
  - **Web Framework:** Dash, Flask
- **Frontend:** Dash (HTML/CSS components)
  - **Plotting:** Plotly Express
- **Data Acquisition:** Requests, lxml (for web scraping S&P 500 list)
- **Deployment:** Gunicorn, PythonAnywhere

## How to Run Locally

1. Clone the repository:
   ```bash
   git clone https://github.com/bethanisk00/Quantitative-Portfolio-Optimizer.git
