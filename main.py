# In app.py

import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import numpy as np

# --- Import Your Backend Logic ---
from data_feeder import get_stock_data
from risk_calculator import calculate_portfolio_returns, calculate_historical_var_es
from portfolio_optimizer import optimize_portfolio, calculate_portfolio_performance
from stock_screener import find_uncorrelated_stocks

# --- App Initialization ---
# The external_stylesheets will automatically link to the style.css in your assets folder
app = dash.Dash(__name__, external_stylesheets=['style.css'])
server = app.server

# --- App Layout ---
app.layout = html.Div(className='app-container', children=[
    
    # Left Column: Inputs
    html.Div(className='left-column', children=[
        html.Div(className='card', children=[
            html.H3("Client Inputs"),
            
            html.Label("Add Stock to Portfolio", className='input-label'),
            html.Div(className='input-row', children=[
                dcc.Input(id='add-ticker-input', placeholder='Ticker', style={'text-transform': 'uppercase'}),
                dcc.Input(id='add-shares-input', placeholder='Shares', type='number', min=1),
                html.Button('Add', id='add-stock-button', n_clicks=0)
            ]),
            html.Div(id='portfolio-list-container'), # This will display the added stocks
            
            html.Label("New Capital to Invest ($)", className='input-label'),
            dcc.Input(id='budget-input', type='number', value=20000, style={'width': '95%'}),
            
            html.Label("Risk Profile", className='input-label', style={'marginTop': '15px'}),
            dcc.Dropdown(id='risk-profile-dropdown',
                options=[{'label': 'Minimum Risk', 'value': 'min_risk'},
                         {'label': 'Balanced (Max Sharpe)', 'value': 'balanced'},
                         {'label': 'High Growth', 'value': 'high_growth'}],
                value='balanced'),
            
            html.Label("Allow Selling of Current Holdings?", className='input-label', style={'marginTop': '15px'}),
            dcc.Dropdown(id='sell-enabled-dropdown',
                options=[{'label': 'Yes', 'value': 'True'}, {'label': 'No', 'value': 'False'}],
                value='True'),
            
            html.Button('Analyze Portfolio', id='submit-button', n_clicks=0)
        ])
    ]),
    
    # Right Column: Outputs
    html.Div(className='right-column', children=[
        html.Div(className='card', children=[
            html.H3("Analysis & Recommendations"),
            dcc.Loading(id="loading-spinner", type="circle",
                children=html.Div(id='results-output', children=["Please add stocks and click 'Analyze Portfolio' to see results."]))
        ])
    ])
])

# --- Callback 1: Add Stock to the Display List ---
@app.callback(
    Output('portfolio-list-container', 'children'),
    Input('add-stock-button', 'n_clicks'),
    State('add-ticker-input', 'value'),
    State('add-shares-input', 'value'),
    State('portfolio-list-container', 'children'),
    prevent_initial_call=True
)
def add_stock_to_list(n_clicks, ticker, shares, current_children):
    if not ticker or not shares or shares <= 0:
        return current_children # Do nothing if inputs are invalid

    new_item = html.Div(f"{ticker.upper()}: {shares}", className='portfolio-item')
    
    if current_children is None:
        return [new_item]
    else:
        return current_children + [new_item]

# --- Callback 2: The Main Analysis ---
@app.callback(
    Output('results-output', 'children'),
    Input('submit-button', 'n_clicks'),
    State('portfolio-list-container', 'children'),
    State('budget-input', 'value'),
    State('risk-profile-dropdown', 'value'),
    State('sell-enabled-dropdown', 'value'),
    prevent_initial_call=True
)
def update_analysis(n_clicks, portfolio_items, budget, risk_profile, sell_enabled_str):
    if not portfolio_items:
        return html.Div("Error: Please add at least one stock to the portfolio.", style={'color': 'red'})

    # --- 1. Parse Inputs ---
    holdings = {}
    for item in portfolio_items:
        text = item['props']['children']
        ticker, shares = text.split(':')
        holdings[ticker.strip()] = int(shares.strip())

    sell_enabled = (sell_enabled_str == 'True')
    tickers = list(holdings.keys())

    # --- 2. Run Backend Logic ---
    try:
        START_DATE, END_DATE = '2021-01-01', '2023-12-31'
        CONFIDENCE_LEVEL, RISK_FREE_RATE = 0.99, 0.02
        
        price_data = get_stock_data(tickers, START_DATE, END_DATE)
        if price_data.empty: return html.Div("Error: Could not fetch data for one or more tickers.", style={'color': 'red'})
        
        latest_prices = price_data.iloc[-1]
        
        # --- SINGLE-STOCK GUARD CLAUSE ---
        if len(tickers) == 1:
            ticker = tickers[0]
            current_shares = holdings[ticker]
            current_value = current_shares * latest_prices.iloc[0]
            new_total_value = current_value + budget
            target_shares = int(np.floor(new_total_value / latest_prices.iloc[0]))
            
            summary_df = pd.DataFrame({
                'Ticker': [ticker],
                'Current Shares': [current_shares],
                'Target Shares': [target_shares],
                'Action': [f"BUY {target_shares - current_shares}"]
            })
            
            final_value = target_shares * latest_prices.iloc[0]
            
            return [
                html.H4("Single Stock Analysis"),
                html.P("Portfolio optimization is not applicable for a single stock. The full budget will be allocated to this asset."),
                dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in summary_df.columns],
                    data=summary_df.to_dict('records'),
                    style_cell={'textAlign': 'left', 'padding': '5px'},
                    style_header={'fontWeight': 'bold'}
                ),
                html.P(f"Final Portfolio Value: ${final_value:,.2f}", style={'marginTop': '20px', 'fontWeight': 'bold'}),
                html.P(f"Leftover Cash: ${(new_total_value - final_value):,.2f}")
            ]

        # --- MULTI-STOCK OPTIMIZATION LOGIC ---
        current_shares = pd.Series(holdings, index=tickers)
        current_dollar_values = current_shares * latest_prices
        current_total_value = current_dollar_values.sum()
        current_weights = current_dollar_values / current_total_value if current_total_value > 0 else pd.Series([0.0]*len(tickers), index=tickers)
        
        returns = price_data.pct_change().dropna()
        mean_returns = returns.mean()
        cov_matrix = returns.cov()
        
        optimal_weights = optimize_portfolio(mean_returns, cov_matrix, risk_profile, RISK_FREE_RATE, current_weights.values, 0.35, sell_enabled)
        
        new_total_value = current_total_value + budget
        optimal_dollar_allocation = new_total_value * optimal_weights
        optimal_shares_target = np.floor(optimal_dollar_allocation / latest_prices)
        
        # --- 3. Prepare DataFrames for Display ---
        trades_required = optimal_shares_target - current_shares
        action_plan_df = pd.DataFrame({'Ticker': tickers, 'Current Shares': current_shares.astype(int), 
                                       'Target Shares': optimal_shares_target.astype(int),
                                       'Action': [f"BUY {int(s)}" if s > 0 else f"SELL {abs(int(s))}" if s < 0 else "HOLD" for s in trades_required.values]})
        
        target_dollar_values = optimal_shares_target * latest_prices
        actual_target_value = target_dollar_values.sum()
        target_allocations = target_dollar_values / actual_target_value if actual_target_value > 0 else pd.Series([0.0]*len(tickers), index=tickers)
        
        allocation_df = pd.DataFrame({
            'Ticker': tickers, 
            'Target Shares': list(optimal_shares_target.astype(int)),
            'Target Value ($)': list(target_dollar_values.astype(float)),
            'Allocation': list(target_allocations.astype(float))
        })
        
        # --- 4. Create Output Components ---
        action_plan_table = dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in action_plan_df.columns],
            data=action_plan_df.to_dict('records'),
            style_data_conditional=[
                {'if': {'filter_query': '{Action} contains "BUY"'}, 'color': '#28a745', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{Action} contains "SELL"'}, 'color': '#dc3545', 'fontWeight': 'bold'}
            ],
            style_cell={'textAlign': 'left', 'padding': '5px'},
            style_header={'fontWeight': 'bold'}
        )
        
        allocation_table = dash_table.DataTable(
            columns=[
                {"name": "Ticker", "id": "Ticker"},
                {"name": "Target Shares", "id": "Target Shares"},
                {"name": "Target Value ($)", "id": "Target Value ($)", "type": "numeric", 
                 "format": dash.dash_table.Format.Format(scheme='fixed', precision=2, group=',', symbol='$')},
                {"name": "Allocation", "id": "Allocation", "type": "numeric", 
                 "format": dash.dash_table.FormatTemplate.percentage(2)}
            ],
            data=allocation_df.to_dict('records'),
            style_cell={'textAlign': 'left', 'padding': '5px'},
            style_header={'fontWeight': 'bold'}
        )
        
        return [
            html.H4("Action Plan: Trades to Reach Optimal Portfolio"),
            action_plan_table,
            html.H4("Final Target Portfolio Allocation", style={'marginTop': '30px'}),
            allocation_table
        ]

    except Exception as e:
        return html.Div(f"An error occurred during analysis: {e}", style={'color': 'red'})


# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True)```