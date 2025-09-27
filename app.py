# In app.py

import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import numpy as np
import plotly.express as px

# --- Import Your Backend Logic ---
from data_feeder import get_stock_data
from risk_calculator import calculate_portfolio_returns, calculate_historical_var_es
from portfolio_optimizer import get_final_allocation, calculate_portfolio_performance
from ticker_fetcher import get_sp500_tickers
from stock_screener import find_uncorrelated_stocks
from data_cacher import get_sp500_price_data # <-- ADD THIS IMPORT
from datetime import date, timedelta # <-- ADD THIS IMPORT
# --- Load Data on App Startup ---
sp500_options, sp500_lookup_df = get_sp500_tickers()

# --- App Initialization ---
app = dash.Dash(__name__, external_stylesheets=['style.css'])
server = app.server

# --- App Layout (No changes needed) ---
app.layout = html.Div([
    html.H1("Quantitative Portfolio Optimizer"),
    dcc.Store(id='intermediate-data-store'),
    
    html.Div(className='app-container', children=[
        # Left Column: Inputs
        html.Div(className='left-column', children=[
            html.Div(className='card', children=[
                html.H3("1. Build Your Current Portfolio"),
                html.Label("Search and Select a Stock", className='input-label'),
                html.Div(className='input-row', children=[
                    dcc.Dropdown(id='add-ticker-dropdown', options=sp500_options, placeholder='Type to search...'),
                    dcc.Input(id='add-shares-input', placeholder='Shares', type='number', n_submit=0),
                    html.Button('Add', id='add-stock-button', n_clicks=0, className='button')
                ]),
                html.Div(id='portfolio-list-container'),
                html.Button('Analyze Current Portfolio', id='analyze-button', n_clicks=0, className='button', style={'width': '100%', 'marginTop': '20px', 'backgroundColor': '#007bff'})
            ]),
            html.Div(id='optimization-card', className='card', style={'display': 'none'}, children=[
                html.H3("2. Define Optimization Goal"),
                html.Label("Select stocks to include in optimization:", className='input-label'),
                dcc.Checklist(id='candidate-checklist', options=[], value=[], labelStyle={'display': 'block', 'marginBottom': '5px'}),
                html.Label("New Capital to Invest ($)", className='input-label', style={'marginTop': '15px'}),
                dcc.Input(id='budget-input', type='number', value=20000, style={'width': '95%'}),
                html.Label("Risk Profile", className='input-label', style={'marginTop': '15px'}),
                dcc.Dropdown(id='risk-profile-dropdown',
                    options=[
                        {'label': 'Minimum Risk', 'value': 'min_risk'},
                        {'label': 'Balanced (Risk Parity)', 'value': 'balanced'},
                        {'label': 'High Growth (Return Target)', 'value': 'high_growth'}
                    ],
                    value='balanced'),
                html.Label("Allow Selling?", className='input-label', style={'marginTop': '15px'}),
                dcc.Dropdown(id='sell-enabled-dropdown',
                    options=[{'label': 'Yes', 'value': 'True'}, {'label': 'No', 'value': 'False'}],
                    value='True'),
                html.Button('Find Optimal Portfolio', id='optimize-button', n_clicks=0, className='button', style={'width': '100%', 'marginTop': '20px'})
            ])
        ]),
        # Right Column: Outputs
        html.Div(className='right-column', children=[
            html.Div(className='card', children=[
                html.H3("Analysis & Recommendations"),
                dcc.Loading(id="loading-spinner", type="circle",
                    children=html.Div(id='results-output', children=["Build your portfolio and click 'Analyze' to begin."]))
            ])
        ])
    ])
])

# --- Callback to add stocks to the list (No changes needed) ---
@app.callback(
    Output('portfolio-list-container', 'children'),
    [Input('add-stock-button', 'n_clicks'), Input('add-shares-input', 'n_submit')],
    [State('add-ticker-dropdown', 'value'), State('add-shares-input', 'value'), State('portfolio-list-container', 'children')],
    prevent_initial_call=True
)
def add_stock_to_list(n_clicks, n_submit, ticker, shares, current_children):
    if not ticker or not isinstance(shares, (int, float)) or shares <= 0: return current_children
    new_item = html.Div(f"{ticker.upper()}: {int(shares)}", className='portfolio-item')
    return (current_children or []) + [new_item]

# --- Callback for STAGE 1 (with 12m Return feature restored) ---
@app.callback(
    Output('results-output', 'children'),
    Output('optimization-card', 'style'),
    Output('candidate-checklist', 'options'),
    Output('candidate-checklist', 'value'),
    Output('intermediate-data-store', 'data'),
    Input('analyze-button', 'n_clicks'),
    State('portfolio-list-container', 'children'),
    prevent_initial_call=True
)
def analyze_current_portfolio(n_clicks, portfolio_items):
    if not portfolio_items:
        return html.Div("Please add stocks to your portfolio first."), {'display': 'none'}, [], [], {}
    
    holdings = {item['props']['children'].split(':')[0].strip(): int(item['props']['children'].split(':')[1].strip()) for item in portfolio_items}
    tickers = list(holdings.keys())
    
    try:
        END_DATE = date.today().strftime('%Y-%m-%d')
        START_DATE = date.today().replace(year=date.today().year - 2).strftime('%Y-%m-%d')
        CONFIDENCE_LEVEL = 0.99        
        price_data = get_stock_data(tickers, START_DATE, END_DATE)
        if price_data.empty: return html.Div("Error fetching price data."), {'display': 'none'}, [], [], {}

        latest_prices = price_data.iloc[-1] 
        current_shares = pd.Series(holdings, index=tickers)
        current_dollar_values = current_shares * latest_prices
        current_total_value = current_dollar_values.sum()
        current_weights = current_dollar_values / current_total_value if current_total_value > 0 else pd.Series([0.0]*len(tickers), index=tickers)
        returns = price_data.pct_change().dropna()
        mean_returns = returns.mean()
        cov_matrix = returns.cov()
        current_returns_ts = calculate_portfolio_returns(price_data, current_weights.values)
        current_hist_var, _ = calculate_historical_var_es(current_returns_ts, CONFIDENCE_LEVEL)
        current_ann_return, current_ann_volatility = calculate_portfolio_performance(current_weights.values, mean_returns, cov_matrix)

        if current_ann_volatility < 0.15: risk_level, risk_color = "Low Risk", "#28a745"
        elif 0.15 <= current_ann_volatility < 0.25: risk_level, risk_color = "Moderate Risk", "#fd7e14"
        else: risk_level, risk_color = "High Risk", "#dc3545"
            
        # --- THIS IS THE UPGRADE TO THE HEDGING TABLE ---
        hedging_suggestions = find_uncorrelated_stocks(current_returns_ts, START_DATE, END_DATE)
        
        suggested_tickers = hedging_suggestions.index.tolist()
        sp500_prices = get_sp500_price_data(START_DATE, END_DATE)
        
        if not sp500_prices.empty and suggested_tickers:
            suggested_prices = sp500_prices[suggested_tickers].last('365D')
            if len(suggested_prices) > 1:
                returns_12m = (suggested_prices.iloc[-1] - suggested_prices.iloc[0]) / suggested_prices.iloc[0]
                returns_12m.name = '12m Return'
                hedging_suggestions = pd.merge(hedging_suggestions, returns_12m, left_index=True, right_index=True, how='left')

        hedging_df = hedging_suggestions.reset_index().rename(columns={'index': 'Ticker'})
        merged_df = pd.merge(hedging_df, sp500_lookup_df, on='Ticker', how='left')
        
        # Add a check for the '12m Return' column before filling NAs
        if '12m Return' not in merged_df.columns: merged_df['12m Return'] = np.nan
        merged_df['12m Return'].fillna(0, inplace=True)
        
        final_hedging_df = merged_df[['Ticker', 'Company Name', 'Correlation', '12m Return']]
        
        hedging_table = dash_table.DataTable(
            columns=[
                {"name": "Ticker", "id": "Ticker"},
                {"name": "Company Name", "id": "Company Name"},
                {"name": "Correlation", "id": "Correlation", "type": "numeric", "format": dash_table.Format.Format(precision=3, scheme='f')},
                {"name": "12m Return", "id": "12m Return", "type": "numeric", "format": dash_table.FormatTemplate.percentage(2)}
            ],
            data=final_hedging_df.to_dict('records'),
            style_cell={'textAlign': 'left', 'padding': '5px'},
            style_header={'backgroundColor': 'var(--primary-color)', 'color': 'white', 'fontWeight': 'bold'}
        )
        
        intermediate_data = {'holdings': holdings, 'original_tickers': tickers, 'original_total_value': current_total_value}
        
        current_options = [{'label': t, 'value': t} for t in tickers]
        suggested_options = [{'label': f"{row['Ticker']} (Corr: {row['Correlation']:.2f}, Ret: {row['12m Return']:.1%})", 'value': row['Ticker']} for index, row in final_hedging_df.iterrows()]
        
        checklist_options = current_options + suggested_options
        checklist_values = tickers
        
        results_layout = html.Div([
            html.Div(className='kpi-container', children=[
                html.Div(className='kpi-card', children=[
                    html.P("Est. Annualized Return", className='kpi-title'), html.P(f"{current_ann_return:.2%}", className='kpi-value')]),
                html.Div(className='kpi-card', children=[
                    html.P("Annualized Volatility (Risk)", className='kpi-title'), html.P(f"{current_ann_volatility:.2%}", className='kpi-value')]),
                html.Div(className='kpi-card', children=[
                    html.P(f"Historical VaR ({CONFIDENCE_LEVEL:.0%})", className='kpi-title'), html.P(f"{current_hist_var:.2%}", className='kpi-value')])
            ]),
            html.Div(className='risk-profile-container', style={'backgroundColor': risk_color}, children=[
                html.P("Your Current Portfolio Risk Profile is:", className='risk-profile-title'), html.P(risk_level, className='risk-profile-text')]),
            html.Hr(),
            html.H4("Hedging & Diversification Suggestions"),
            html.P("Consider adding one of these S&P 500 stocks to potentially reduce risk."),
            hedging_table,
            html.Hr(),
            html.P("Now, select the stocks to include in the optimization below and define your goal.", style={'textAlign': 'center', 'fontStyle': 'italic'})
        ])
        
        return results_layout, {'display': 'block'}, checklist_options, checklist_values, intermediate_data

    except Exception as e:
        import traceback
        return html.Div([html.H4("An unexpected error occurred during analysis:"), html.Pre(f"{e}\n\n{traceback.format_exc()}")]), {'display': 'none'}, [], [], {}

# --- Callback for STAGE 2: Run Final Optimization (No changes needed) ---
@app.callback(
    Output('results-output', 'children', allow_duplicate=True),
    Input('optimize-button', 'n_clicks'),
    State('candidate-checklist', 'value'),
    State('budget-input', 'value'),
    State('risk-profile-dropdown', 'value'),
    State('sell-enabled-dropdown', 'value'),
    State('intermediate-data-store', 'data'),
    prevent_initial_call=True
)
def run_final_optimization(n_clicks, candidate_tickers, budget, risk_profile, sell_enabled_str, intermediate_data):
    if not candidate_tickers:
        return html.Div("Please select at least one stock for optimization.", style={'color': 'red'})

    holdings = intermediate_data.get('holdings', {})
    original_tickers = intermediate_data.get('original_tickers', [])
    original_total_value = intermediate_data.get('original_total_value', 0)
    sell_enabled = (sell_enabled_str == 'True')
    
    try:
        END_DATE = date.today().strftime('%Y-%m-%d')
        START_DATE = (date.today() - timedelta(days=2*365)).strftime('%Y-%m-%d')
        RISK_FREE_RATE = 0.02        
        # --- 1. DATA PREP (Original Portfolio for "Before" Chart) ---
        original_price_data = get_stock_data(original_tickers, START_DATE, END_DATE)
        # Ensure we proceed only if we have data
        if original_price_data.empty and original_tickers:
            return html.Div("Error fetching data for the original portfolio.")
        original_latest_prices = original_price_data.iloc[-1]
        original_shares = pd.Series({t: holdings.get(t, 0) for t in original_tickers}, index=original_tickers)
        original_dollar_values = original_shares * original_latest_prices
        original_weights = original_dollar_values / original_total_value if original_total_value > 0 else pd.Series([0.0]*len(original_tickers), index=original_tickers)

        # --- 2. DATA PREP (Candidate Portfolio for Optimization) ---
        candidate_price_data = get_stock_data(candidate_tickers, START_DATE, END_DATE)
        if candidate_price_data.empty: return html.Div("Error: Could not fetch data for selected candidates.", style={'color': 'red'})
        
        latest_prices = candidate_price_data.iloc[-1]
        
        # --- THIS IS THE DEFINITIVE FIX ---
        # Ensure the latest_prices Series is ALWAYS in the same order as candidate_tickers
        latest_prices = latest_prices.reindex(candidate_tickers)
        
        # Now, all subsequent calculations are guaranteed to be aligned.
        candidate_current_shares = pd.Series({t: holdings.get(t, 0) for t in candidate_tickers}, index=candidate_tickers)
        candidate_current_dollar_values = candidate_current_shares * latest_prices
        candidate_current_total_value = candidate_current_dollar_values.sum()
        candidate_current_weights = candidate_current_dollar_values / candidate_current_total_value if candidate_current_total_value > 0 else pd.Series([0.0]*len(candidate_tickers), index=candidate_tickers)
        
        returns = candidate_price_data.pct_change().dropna()
        mean_returns = returns.mean()
        cov_matrix = returns.cov()
        
        final_weights = get_final_allocation(mean_returns, cov_matrix, risk_profile, RISK_FREE_RATE, candidate_current_weights.values, 0.35, sell_enabled)
        
        new_total_value = original_total_value + budget
        optimal_dollar_allocation = new_total_value * final_weights
        
        # This calculation is now correct because latest_prices is properly ordered.
        optimal_shares_target = np.floor(optimal_dollar_allocation / latest_prices)
        # --- END OF FIX ---
        
        trades_required = optimal_shares_target - candidate_current_shares
        action_plan_df = pd.DataFrame({'Ticker': candidate_tickers, 'Current Shares': list(candidate_current_shares.astype(int)), 'Target Shares': list(optimal_shares_target.astype(int)), 'Action': [f"BUY {int(s)}" if s > 0 else f"SELL {abs(int(s))}" if s < 0 else "HOLD" for s in trades_required.values]})
        
        target_dollar_values = optimal_shares_target * latest_prices
        actual_target_value = target_dollar_values.sum()
        final_allocations = target_dollar_values / actual_target_value if actual_target_value > 0 else pd.Series([0.0]*len(candidate_tickers), index=candidate_tickers)
        allocation_df = pd.DataFrame({'Ticker': candidate_tickers, 'Target Value ($)': list(target_dollar_values.astype(float)), 'Allocation': list(final_allocations.astype(float))})
        
        # Create the "before" pie chart using only the original tickers and data
        original_price_data = get_stock_data(original_tickers, START_DATE, END_DATE)
        original_latest_prices = original_price_data.iloc[-1]
        original_shares = pd.Series({t: holdings.get(t, 0) for t in original_tickers})
        original_dollar_values = original_shares * original_latest_prices
        original_weights = original_dollar_values / original_total_value if original_total_value > 0 else pd.Series([0.0]*len(original_tickers), index=original_tickers)

        pie_charts = html.Div(className='pie-chart-container', children=[
            dcc.Graph(figure=px.pie(names=original_tickers, values=original_weights, title='Original Portfolio Allocation', hole=.3)),
            dcc.Graph(figure=px.pie(names=candidate_tickers, values=final_allocations, title='New Optimal Allocation', hole=.3))
        ])
        
        action_plan_table = dash_table.DataTable(
                    columns=[{"name": "Ticker", "id": "Ticker", "type": "text"}, {"name": "Current Shares", "id": "Current Shares", "type": "numeric"}, {"name": "Target Shares", "id": "Target Shares", "type": "numeric"}, {"name": "Action", "id": "Action", "type": "text"}],
                    data=action_plan_df.to_dict('records'),
                    style_data_conditional=[{'if': {'filter_query': '{Action} contains "BUY"'}, 'color': '#28a745', 'fontWeight': 'bold'}, {'if': {'filter_query': '{Action} contains "SELL"'}, 'color': '#dc3545', 'fontWeight': 'bold'}],
                    style_cell={'textAlign': 'left', 'padding': '5px'},
                    style_header={'backgroundColor': '#4a47a3', 'color': 'white', 'fontWeight': 'bold'}
                )
        
        allocation_table = dash_table.DataTable(
            columns=[{"name": "Ticker", "id": "Ticker"}, {"name": "Target Value ($)", "id": "Target Value ($)", "type": "numeric", "format": dash_table.Format.Format(precision=2, scheme='f', symbol='$')}, {"name": "Allocation", "id": "Allocation", "type": "numeric", "format": dash_table.FormatTemplate.percentage(2)}],
            data=allocation_df.to_dict('records'),
            style_cell={'textAlign': 'left', 'padding': '5px'},
            style_header={'backgroundColor': '#4a47a3', 'color': 'white', 'fontWeight': 'bold'}
        )

        return [
            pie_charts,
            html.H4("Action Plan", style={'marginTop': '30px'}),
            action_plan_table,
            html.H4("Final Target Allocation", style={'marginTop': '30px'}),
            allocation_table
        ]

    except Exception as e:
        import traceback
        return html.Div([html.H4("An unexpected error occurred..."), html.Pre(f"{e}\n\n{traceback.format_exc()}")])


# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True)