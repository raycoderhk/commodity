"""
China Commodity Price Dashboard
Streamlit web application to view and query commodity prices in China (RMB).
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
from data_fetcher import (
    fetch_commodity_data,
    get_available_commodities,
    get_commodity_display_name,
    get_commodity_category,
    get_categories,
    get_commodities_by_category,
    COMMODITY_MAP
)

# Page configuration
st.set_page_config(
    page_title="China Commodity Price Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("📊 China Commodity Price Dashboard")
st.markdown("View and analyze commodity prices from Shanghai Futures Exchange (SHFE) and Dalian Commodity Exchange (DCE) in RMB")

# Sidebar
st.sidebar.header("Filters")

# Commodity selection with categories
commodity_display_names = {c: get_commodity_display_name(c) for c in get_available_commodities()}
categorized_commodities = get_commodities_by_category()
categories = get_categories()

# Default expanded categories
default_expanded_categories = ['Base Metals', 'Paper & Wood Products']

# Initialize session state for category expansion
if 'category_expanded' not in st.session_state:
    st.session_state.category_expanded = {cat: (cat in default_expanded_categories) for cat in categories}

# Initialize session state for all commodities
default_selected = ['copper', 'aluminum', 'zinc']  # Default selection
all_commodities = get_available_commodities()
for commodity in all_commodities:
    if f"commodity_{commodity}" not in st.session_state:
        st.session_state[f"commodity_{commodity}"] = commodity in default_selected

# Allow multiple selection using checkboxes grouped by category
st.sidebar.markdown("**Select Commodities:**")

# Control to expand/collapse all categories
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("Expand All", use_container_width=True):
        for cat in categories:
            st.session_state.category_expanded[cat] = True
        st.rerun()
with col2:
    if st.button("Collapse All", use_container_width=True):
        for cat in categories:
            st.session_state.category_expanded[cat] = False
        st.rerun()

selected_commodities = []

# Display commodities grouped by category
for category in categories:
    commodities_in_category = categorized_commodities.get(category, [])
    if commodities_in_category:
        # Get expanded state from session state
        should_expand = st.session_state.category_expanded.get(category, category in default_expanded_categories)
        
        with st.sidebar.expander(f"📁 {category} ({len(commodities_in_category)})", expanded=should_expand):
            # Check if all commodities in THIS category are selected
            category_commodity_states = [st.session_state[f"commodity_{c}"] for c in commodities_in_category]
            all_selected_in_category = all(category_commodity_states)
            
            # Toggle button for Select All/Unselect All (only affects this category)
            button_label = "Unselect All" if all_selected_in_category else "Select All"
            button_clicked = st.button(button_label, key=f"toggle_all_{category}", use_container_width=True)
            
            if button_clicked:
                # Toggle state: if all selected, unselect all; if not all selected, select all
                new_state = not all_selected_in_category
                # CRITICAL: Only update commodities in THIS specific category
                # Store which category was toggled to prevent processing others
                for commodity in commodities_in_category:
                    st.session_state[f"commodity_{commodity}"] = new_state
                # Immediately rerun to prevent processing other categories
                st.rerun()
            
            # Compact spacing for checkboxes
            for commodity in sorted(commodities_in_category, key=lambda x: commodity_display_names[x]):
                checkbox_value = st.checkbox(
                    commodity_display_names[commodity],
                    value=st.session_state[f"commodity_{commodity}"],
                    key=f"commodity_{commodity}"
                )
                if checkbox_value:
                    selected_commodities.append(commodity)

# Date range selection
st.sidebar.markdown("---")
st.sidebar.markdown("**Date Range**")

# Initialize session state for date range if not exists
if 'date_range_selected' not in st.session_state:
    st.session_state.date_range_selected = '5 years'
if 'custom_date_range' not in st.session_state:
    st.session_state.custom_date_range = None

default_end = datetime.now()

# Predefined date range buttons
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("1 Month", use_container_width=True):
        st.session_state.date_range_selected = '1 month'
        st.session_state.custom_date_range = None
    if st.button("1 Year", use_container_width=True):
        st.session_state.date_range_selected = '1 year'
        st.session_state.custom_date_range = None
with col2:
    if st.button("2 Years", use_container_width=True):
        st.session_state.date_range_selected = '2 years'
        st.session_state.custom_date_range = None
    if st.button("5 Years", use_container_width=True):
        st.session_state.date_range_selected = '5 years'
        st.session_state.custom_date_range = None

# Calculate start date based on selected range
range_days = {
    '1 month': 30,
    '1 year': 365,
    '2 years': 2 * 365,
    '5 years': 5 * 365
}

selected_range = st.session_state.date_range_selected
default_start = default_end - timedelta(days=range_days.get(selected_range, 5 * 365))

# Date input for custom range
if st.session_state.custom_date_range is None:
    date_range_value = (default_start.date(), default_end.date())
else:
    date_range_value = st.session_state.custom_date_range

date_range = st.sidebar.date_input(
    "Or Select Custom Range",
    value=date_range_value,
    min_value=default_start.date(),
    max_value=default_end.date()
)

# Update session state if custom range is selected
if isinstance(date_range, tuple) and len(date_range) == 2:
    if date_range != date_range_value:
        st.session_state.custom_date_range = date_range
        st.session_state.date_range_selected = 'custom'
    start_date, end_date = date_range
    start_date = datetime.combine(start_date, datetime.min.time())
    end_date = datetime.combine(end_date, datetime.max.time())
else:
    start_date = datetime.combine(default_start.date(), datetime.min.time())
    end_date = datetime.combine(default_end.date(), datetime.max.time())

st.sidebar.markdown("---")
st.sidebar.markdown("**Display Options**")
show_statistics = st.sidebar.checkbox("Show Statistics", value=True)
show_trends = st.sidebar.checkbox("Show Trend Analysis", value=False)
moving_average_days = st.sidebar.slider("Moving Average Period (days)", 7, 90, 30)

# Main content
if not selected_commodities:
    st.warning("Please select at least one commodity from the sidebar.")
    st.stop()

# Fetch data
st.subheader("Price Charts")
data_container = st.container()

all_data = {}
with st.spinner("Fetching commodity price data..."):
    for commodity in selected_commodities:
        df = fetch_commodity_data(commodity, start_date, end_date, use_cache=True)
        if not df.empty:
            all_data[commodity] = df
        else:
            st.warning(f"⚠️ No data available for {commodity_display_names[commodity]}")

if not all_data:
    st.error("No data available for the selected commodities and date range.")
    st.stop()

# Calculate historical prices
st.subheader("Historical Price Comparison")

# Build table data
table_data = []
for commodity, df in all_data.items():
    if not df.empty:
        display_name = commodity_display_names[commodity]
        prices = df['price']
        dates = df['date']
        
        # Current price (most recent)
        current_price = prices.iloc[-1]
        current_date = dates.iloc[-1]
        
        # Fetch extended historical data for comparison (go back 5+ years from current date)
        extended_start_date = current_date - timedelta(days=365 * 6)  # 6 years to ensure we have 5 years
        extended_df = fetch_commodity_data(commodity, extended_start_date, current_date, use_cache=True)
        
        # Use extended data if available, otherwise fall back to original df
        comparison_df = extended_df if not extended_df.empty else df
        
        # Get prices at different time points (1, 2, 3, 4, 5 years ago)
        row_data = {'Commodity': display_name, 'Current': f"¥{current_price:,.2f}"}
        
        for years_back in range(1, 6):  # 1 to 5 years ago
            target_date = current_date - timedelta(days=365 * years_back)
            # Find closest date to target date (within ±30 days for flexibility)
            historical_data = comparison_df[
                (comparison_df['date'] >= target_date - timedelta(days=30)) &
                (comparison_df['date'] <= target_date + timedelta(days=30))
            ]
            
            if not historical_data.empty:
                # Get the closest date to target
                historical_data = historical_data.copy()
                historical_data['date_diff'] = abs((historical_data['date'] - target_date).dt.days)
                closest_row = historical_data.loc[historical_data['date_diff'].idxmin()]
                historical_price = closest_row['price']
                row_data[f'{years_back}Y Ago'] = f"¥{historical_price:,.2f}"
            else:
                # Fallback: try to find any data before target date
                fallback_data = comparison_df[comparison_df['date'] <= target_date]
                if not fallback_data.empty:
                    historical_price = fallback_data['price'].iloc[-1]
                    row_data[f'{years_back}Y Ago'] = f"¥{historical_price:,.2f}"
                else:
                    row_data[f'{years_back}Y Ago'] = "N/A"
        
        table_data.append(row_data)

# Display compact table
if table_data:
    df_table = pd.DataFrame(table_data)
    st.dataframe(df_table, use_container_width=True, hide_index=True)

st.markdown("---")

# Create interactive chart
fig = go.Figure()

colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

for idx, (commodity, df) in enumerate(all_data.items()):
    color = colors[idx % len(colors)]
    display_name = commodity_display_names[commodity]
    
    # Main price line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['price'],
        mode='lines',
        name=display_name,
        line=dict(color=color, width=2),
        hovertemplate=f'<b>{display_name}</b><br>' +
                      'Date: %{x}<br>' +
                      'Price: ¥%{y:,.2f} RMB<extra></extra>',
        showlegend=True
    ))
    
    # Add label at the end of the line with offset to prevent overlap
    if not df.empty:
        last_date = df['date'].iloc[-1]
        last_price = df['price'].iloc[-1]
        
        # Calculate offset based on index to stagger labels vertically
        # Alternate between slight up and down offset
        y_offset = (idx % 3 - 1) * (df['price'].max() - df['price'].min()) * 0.02
        
        # Add annotation with better positioning
        fig.add_annotation(
            x=last_date,
            y=last_price + y_offset,
            text=display_name,
            showarrow=False,
            xshift=10,  # Push label to the right
            bgcolor="rgba(255, 255, 255, 0.8)",  # Semi-transparent white background
            bordercolor=color,
            borderwidth=1,
            borderpad=3,
            font=dict(color=color, size=10),
            xanchor='left'
        )
    
    # Moving average if enabled
    if show_trends and len(df) >= moving_average_days:
        ma = df['price'].rolling(window=moving_average_days).mean()
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=ma,
            mode='lines',
            name=f'{display_name} MA({moving_average_days})',
            line=dict(color=color, width=1, dash='dash'),
            opacity=0.6,
            hovertemplate=f'<b>{display_name} MA</b><br>' +
                          'Date: %{x}<br>' +
                          'MA: ¥%{y:,.2f} RMB<extra></extra>',
            showlegend=True
        ))

fig.update_layout(
    title="Commodity Prices Over Time (RMB)",
    xaxis_title="Date",
    yaxis_title="Price (RMB)",
    hovermode='x unified',
    height=600,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# Statistics panel
if show_statistics:
    st.subheader("Statistics")
    
    # Determine number of columns per row based on number of commodities
    # Use 3-4 columns per row for better readability
    num_commodities = len(all_data)
    if num_commodities <= 3:
        cols_per_row = num_commodities
    elif num_commodities <= 6:
        cols_per_row = 3
    elif num_commodities <= 9:
        cols_per_row = 3
    else:
        cols_per_row = 4  # Max 4 columns per row
    
    # Create rows dynamically
    commodities_list = list(all_data.items())
    for row_start in range(0, num_commodities, cols_per_row):
        row_end = min(row_start + cols_per_row, num_commodities)
        row_commodities = commodities_list[row_start:row_end]
        stats_cols = st.columns(len(row_commodities))
        
        for col_idx, (commodity, df) in enumerate(row_commodities):
            with stats_cols[col_idx]:
                display_name = commodity_display_names[commodity]
                st.markdown(f"### {display_name}")
                
                if not df.empty:
                    prices = df['price']
                    
                    # Calculate statistics
                    avg_price = prices.mean()
                    min_price = prices.min()
                    max_price = prices.max()
                    current_price = prices.iloc[-1]
                    first_price = prices.iloc[0]
                    pct_change = ((current_price - first_price) / first_price) * 100
                    
                    # Volatility (standard deviation)
                    volatility = prices.std()
                    volatility_pct = (volatility / avg_price) * 100
                    
                    # Display metrics
                    st.metric("Current Price", f"¥{current_price:,.2f}", f"{pct_change:+.2f}%")
                    st.metric("Average Price", f"¥{avg_price:,.2f}")
                    st.metric("Min Price", f"¥{min_price:,.2f}")
                    st.metric("Max Price", f"¥{max_price:,.2f}")
                    st.metric("Volatility", f"¥{volatility:,.2f}", f"{volatility_pct:.2f}%")
                    
                    # Price range
                    price_range = max_price - min_price
                    st.metric("Price Range", f"¥{price_range:,.2f}")

# Trend analysis
if show_trends:
    st.subheader("Trend Analysis")
    
    # Use same column layout as statistics for consistency
    num_commodities = len(all_data)
    if num_commodities <= 3:
        cols_per_row = num_commodities
    elif num_commodities <= 6:
        cols_per_row = 3
    elif num_commodities <= 9:
        cols_per_row = 3
    else:
        cols_per_row = 4
    
    # Create rows dynamically
    commodities_list = list(all_data.items())
    for row_start in range(0, num_commodities, cols_per_row):
        row_end = min(row_start + cols_per_row, num_commodities)
        row_commodities = commodities_list[row_start:row_end]
        trend_cols = st.columns(len(row_commodities))
        
        for col_idx, (commodity, df) in enumerate(row_commodities):
            with trend_cols[col_idx]:
                display_name = commodity_display_names[commodity]
                st.markdown(f"#### {display_name}")
                
                if len(df) >= 2:
                    prices = df['price']
                    
                    # Short-term trend (last 30 days vs previous 30 days)
                    if len(prices) >= 60:
                        recent_avg = prices.tail(30).mean()
                        previous_avg = prices.tail(60).head(30).mean()
                        short_trend = ((recent_avg - previous_avg) / previous_avg) * 100
                        trend_direction = "📈 Upward" if short_trend > 0 else "📉 Downward" if short_trend < 0 else "➡️ Stable"
                        st.markdown(f"**Short-term Trend (30 days):** {trend_direction} ({short_trend:+.2f}%)")
                    
                    # Long-term trend (overall period)
                    overall_trend = ((prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0]) * 100
                    trend_direction = "📈 Upward" if overall_trend > 0 else "📉 Downward" if overall_trend < 0 else "➡️ Stable"
                    st.markdown(f"**Overall Trend:** {trend_direction} ({overall_trend:+.2f}%)")
                    
                    # Volatility indicator
                    volatility = prices.std() / prices.mean() * 100
                    if volatility < 5:
                        vol_level = "🟢 Low"
                    elif volatility < 10:
                        vol_level = "🟡 Medium"
                    else:
                        vol_level = "🔴 High"
                    st.markdown(f"**Volatility:** {vol_level} ({volatility:.2f}%)")

# Data table
with st.expander("View Raw Data"):
    for commodity, df in all_data.items():
        st.markdown(f"### {commodity_display_names[commodity]}")
        st.dataframe(df, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("**Data Source:** Shanghai Futures Exchange (SHFE) and Dalian Commodity Exchange (DCE) via akshare")
st.markdown("**Currency:** All prices in RMB (Chinese Yuan)")

