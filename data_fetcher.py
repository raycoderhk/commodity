"""
Data fetching module for Chinese commodity prices from SHFE and DCE exchanges.
Uses akshare library to fetch historical futures data in RMB.
"""

import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
from pathlib import Path
import streamlit as st


# Commodity mapping to exchange and ticker symbols with categories
# Complete list from official SHFE and DCE exchange websites (47 commodities total)
COMMODITY_MAP = {
    # Precious Metals
    'gold': {'exchange': 'SHFE', 'symbol': 'au', 'name': 'Gold', 'category': 'Precious Metals'},
    'silver': {'exchange': 'SHFE', 'symbol': 'ag', 'name': 'Silver', 'category': 'Precious Metals'},
    
    # Base Metals
    'copper': {'exchange': 'SHFE', 'symbol': 'cu', 'name': 'Copper', 'category': 'Base Metals'},
    'bonded_copper': {'exchange': 'SHFE', 'symbol': 'bc', 'name': 'Bonded Copper', 'category': 'Base Metals'},
    'electrolytic_copper': {'exchange': 'SHFE', 'symbol': 'ec', 'name': 'Electrolytic Copper', 'category': 'Base Metals'},
    'aluminum': {'exchange': 'SHFE', 'symbol': 'al', 'name': 'Aluminum', 'category': 'Base Metals'},
    'aluminum_oxide': {'exchange': 'SHFE', 'symbol': 'ao', 'name': 'Aluminum Oxide', 'category': 'Base Metals'},
    'zinc': {'exchange': 'SHFE', 'symbol': 'zn', 'name': 'Zinc', 'category': 'Base Metals'},
    'lead': {'exchange': 'SHFE', 'symbol': 'pb', 'name': 'Lead', 'category': 'Base Metals'},
    'nickel': {'exchange': 'SHFE', 'symbol': 'ni', 'name': 'Nickel', 'category': 'Base Metals'},
    'tin': {'exchange': 'SHFE', 'symbol': 'sn', 'name': 'Tin', 'category': 'Base Metals'},
    
    # Steel Products
    'steel': {'exchange': 'SHFE', 'symbol': 'rb', 'name': 'Steel (Rebar)', 'category': 'Steel Products'},
    'wire_rod': {'exchange': 'SHFE', 'symbol': 'wr', 'name': 'Wire Rod', 'category': 'Steel Products'},
    'hot_rolled_coil': {'exchange': 'SHFE', 'symbol': 'hc', 'name': 'Hot Rolled Coil', 'category': 'Steel Products'},
    'stainless_steel': {'exchange': 'SHFE', 'symbol': 'ss', 'name': 'Stainless Steel', 'category': 'Steel Products'},
    
    # Energy
    'crude_oil': {'exchange': 'SHFE', 'symbol': 'sc', 'name': 'Crude Oil', 'category': 'Energy'},
    'low_sulfur_fuel_oil': {'exchange': 'SHFE', 'symbol': 'lu', 'name': 'Low Sulfur Fuel Oil', 'category': 'Energy'},
    'fuel_oil': {'exchange': 'SHFE', 'symbol': 'fu', 'name': 'Fuel Oil', 'category': 'Energy'},
    'bitumen': {'exchange': 'SHFE', 'symbol': 'bu', 'name': 'Bitumen', 'category': 'Energy'},
    'lpg': {'exchange': 'DCE', 'symbol': 'pg', 'name': 'LPG', 'category': 'Energy'},
    'coke': {'exchange': 'DCE', 'symbol': 'j', 'name': 'Coke', 'category': 'Energy'},
    'coking_coal': {'exchange': 'DCE', 'symbol': 'jm', 'name': 'Coking Coal', 'category': 'Energy'},
    
    # Chemicals & Plastics
    'pvc': {'exchange': 'DCE', 'symbol': 'v', 'name': 'PVC', 'category': 'Chemicals & Plastics'},
    'lldpe': {'exchange': 'DCE', 'symbol': 'l', 'name': 'LLDPE', 'category': 'Chemicals & Plastics'},
    'polypropylene': {'exchange': 'DCE', 'symbol': 'pp', 'name': 'Polypropylene', 'category': 'Chemicals & Plastics'},
    'styrene': {'exchange': 'DCE', 'symbol': 'eb', 'name': 'Styrene', 'category': 'Chemicals & Plastics'},
    'ethylene_glycol': {'exchange': 'DCE', 'symbol': 'eg', 'name': 'Ethylene Glycol', 'category': 'Chemicals & Plastics'},
    
    # Rubber
    'natural_rubber': {'exchange': 'SHFE', 'symbol': 'ru', 'name': 'Natural Rubber', 'category': 'Rubber'},
    'synthetic_rubber': {'exchange': 'SHFE', 'symbol': 'nr', 'name': 'Synthetic Rubber', 'category': 'Rubber'},
    'butadiene_rubber': {'exchange': 'SHFE', 'symbol': 'br', 'name': 'Butadiene Rubber', 'category': 'Rubber'},
    
    # Paper & Wood Products
    'paper_pulp': {'exchange': 'SHFE', 'symbol': 'sp', 'name': 'Paper Pulp', 'category': 'Paper & Wood Products'},
    'offset_paper': {'exchange': 'SHFE', 'symbol': 'op', 'name': 'Offset Paper', 'category': 'Paper & Wood Products'},
    'fiberboard': {'exchange': 'DCE', 'symbol': 'fb', 'name': 'Fiberboard', 'category': 'Paper & Wood Products'},
    'blockboard': {'exchange': 'DCE', 'symbol': 'bb', 'name': 'Blockboard', 'category': 'Paper & Wood Products'},
    
    # Agricultural - Grains & Oilseeds
    'soybean': {'exchange': 'DCE', 'symbol': 'a', 'name': 'Soybean', 'category': 'Agricultural - Grains & Oilseeds'},
    'soybean_no2': {'exchange': 'DCE', 'symbol': 'b', 'name': 'Soybean No.2', 'category': 'Agricultural - Grains & Oilseeds'},
    'soybean_meal': {'exchange': 'DCE', 'symbol': 'm', 'name': 'Soybean Meal', 'category': 'Agricultural - Grains & Oilseeds'},
    'soybean_oil': {'exchange': 'DCE', 'symbol': 'y', 'name': 'Soybean Oil', 'category': 'Agricultural - Grains & Oilseeds'},
    'palm_oil': {'exchange': 'DCE', 'symbol': 'p', 'name': 'Palm Oil', 'category': 'Agricultural - Grains & Oilseeds'},
    'corn': {'exchange': 'DCE', 'symbol': 'c', 'name': 'Corn', 'category': 'Agricultural - Grains & Oilseeds'},
    'corn_starch': {'exchange': 'DCE', 'symbol': 'cs', 'name': 'Corn Starch', 'category': 'Agricultural - Grains & Oilseeds'},
    'rice': {'exchange': 'DCE', 'symbol': 'rr', 'name': 'Rice', 'category': 'Agricultural - Grains & Oilseeds'},
    'long_grain_rice': {'exchange': 'DCE', 'symbol': 'lr', 'name': 'Long-grain Rice', 'category': 'Agricultural - Grains & Oilseeds'},
    'peanut': {'exchange': 'DCE', 'symbol': 'pk', 'name': 'Peanut', 'category': 'Agricultural - Grains & Oilseeds'},
    
    # Agricultural - Livestock & Poultry
    'live_hog': {'exchange': 'DCE', 'symbol': 'lh', 'name': 'Live Hog', 'category': 'Agricultural - Livestock & Poultry'},
    'egg': {'exchange': 'DCE', 'symbol': 'jd', 'name': 'Egg', 'category': 'Agricultural - Livestock & Poultry'},
    
    # Industrial Materials
    'iron_ore': {'exchange': 'DCE', 'symbol': 'i', 'name': 'Iron Ore', 'category': 'Industrial Materials'},
}

# Cache directory
CACHE_DIR = Path('data_cache')
CACHE_DIR.mkdir(exist_ok=True)


def get_cache_path(commodity: str, start_date: str, end_date: str) -> Path:
    """Generate cache file path for a commodity and date range."""
    # Remove dashes from date strings for filename
    start_clean = start_date.replace('-', '')
    end_clean = end_date.replace('-', '')
    cache_file = f"{commodity}_{start_clean}_{end_clean}.csv"
    return CACHE_DIR / cache_file


def fetch_shfe_futures(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch SHFE futures data using akshare.
    
    Args:
        symbol: Commodity symbol (e.g., 'cu', 'al', 'zn', 'rb')
        start_date: Start date in format 'YYYY-MM-DD'
        end_date: End date in format 'YYYY-MM-DD'
    
    Returns:
        DataFrame with historical price data
    """
    try:
        # akshare function requires symbol with '0' suffix for main contract
        # It returns all historical data, we'll filter by date range
        symbol_with_suffix = f"{symbol}0"
        
        # Fetch all historical data
        df = ak.futures_zh_daily_sina(symbol=symbol_with_suffix)
        
        if df is not None and not df.empty:
            # Convert date column to datetime if not already
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            else:
                st.warning(f"Date column not found in data for {symbol}")
                return pd.DataFrame()
            
            # Use 'close' column for price (settlement price)
            if 'close' in df.columns:
                df = df.rename(columns={'close': 'price'})
            elif 'settle' in df.columns:
                df = df.rename(columns={'settle': 'price'})
            else:
                st.warning(f"Price column not found in data for {symbol}")
                return pd.DataFrame()
            
            # Filter by date range
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
            
            # Select only date and price columns
            if 'date' in df.columns and 'price' in df.columns:
                df = df[['date', 'price']].copy()
                df = df.sort_values('date')
                df = df.dropna()
                return df
            
    except Exception as e:
        st.warning(f"Error fetching SHFE data for {symbol}: {str(e)}")
    
    return pd.DataFrame()


def fetch_dce_futures(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch DCE futures data using akshare.
    
    Args:
        symbol: Commodity symbol (e.g., 'v' for PVC)
        start_date: Start date in format 'YYYY-MM-DD'
        end_date: End date in format 'YYYY-MM-DD'
    
    Returns:
        DataFrame with historical price data
    """
    try:
        # DCE futures use the same akshare function as SHFE
        # Symbol needs '0' suffix for main contract
        symbol_with_suffix = f"{symbol}0"
        
        # Fetch all historical data
        df = ak.futures_zh_daily_sina(symbol=symbol_with_suffix)
        
        if df is not None and not df.empty:
            # Convert date column to datetime if not already
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            else:
                st.warning(f"Date column not found in data for {symbol}")
                return pd.DataFrame()
            
            # Use 'close' column for price (settlement price)
            if 'close' in df.columns:
                df = df.rename(columns={'close': 'price'})
            elif 'settle' in df.columns:
                df = df.rename(columns={'settle': 'price'})
            else:
                st.warning(f"Price column not found in data for {symbol}")
                return pd.DataFrame()
            
            # Filter by date range
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
            
            # Select only date and price columns
            if 'date' in df.columns and 'price' in df.columns:
                df = df[['date', 'price']].copy()
                df = df.sort_values('date')
                df = df.dropna()
                return df
                
    except Exception as e:
        st.warning(f"Error fetching DCE data for {symbol}: {str(e)}")
    
    return pd.DataFrame()


def fetch_commodity_data(commodity: str, start_date: datetime, end_date: datetime, use_cache: bool = True) -> pd.DataFrame:
    """
    Fetch historical commodity price data.
    
    Args:
        commodity: Commodity name (e.g., 'copper', 'aluminum', 'pvc')
        start_date: Start date as datetime object
        end_date: End date as datetime object
        use_cache: Whether to use cached data if available
    
    Returns:
        DataFrame with columns: date, price (in RMB)
    """
    if commodity not in COMMODITY_MAP:
        st.error(f"Unknown commodity: {commodity}")
        return pd.DataFrame()
    
    commodity_info = COMMODITY_MAP[commodity]
    symbol = commodity_info['symbol']
    exchange = commodity_info['exchange']
    
    # Format dates for API calls (akshare uses YYYY-MM-DD format)
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    # Check cache
    if use_cache:
        cache_path = get_cache_path(commodity, start_str, end_str)
        if cache_path.exists():
            try:
                df = pd.read_csv(cache_path, parse_dates=['date'])
                # Filter to date range
                df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
                if not df.empty:
                    return df
            except:
                pass
    
    # Fetch from API
    if exchange == 'SHFE':
        df = fetch_shfe_futures(symbol, start_str, end_str)
    elif exchange == 'DCE':
        df = fetch_dce_futures(symbol, start_str, end_str)
    else:
        st.error(f"Unknown exchange: {exchange}")
        return pd.DataFrame()
    
    # Validate and process data
    if df.empty:
        st.warning(f"No data available for {commodity_info['name']}")
        return pd.DataFrame()
    
    # Ensure we have the right columns
    if 'date' not in df.columns or 'price' not in df.columns:
        st.error(f"Unexpected data format for {commodity_info['name']}")
        return pd.DataFrame()
    
    # Filter to date range
    df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    
    # Cache the data
    if use_cache and not df.empty:
        cache_path = get_cache_path(commodity, start_str, end_str)
        df.to_csv(cache_path, index=False)
    
    return df


def get_available_commodities():
    """Return list of available commodity names."""
    return list(COMMODITY_MAP.keys())


def get_commodity_display_name(commodity: str) -> str:
    """Get display name for a commodity."""
    return COMMODITY_MAP.get(commodity, {}).get('name', commodity)


def get_commodity_category(commodity: str) -> str:
    """Get category for a commodity."""
    return COMMODITY_MAP.get(commodity, {}).get('category', 'Other')


def get_categories():
    """Return list of all available categories."""
    categories = set()
    for commodity_info in COMMODITY_MAP.values():
        if 'category' in commodity_info:
            categories.add(commodity_info['category'])
    return sorted(list(categories))


def get_commodities_by_category():
    """Return dictionary of commodities grouped by category."""
    categorized = {}
    for commodity, info in COMMODITY_MAP.items():
        category = info.get('category', 'Other')
        if category not in categorized:
            categorized[category] = []
        categorized[category].append(commodity)
    return categorized

