# China Commodity Price Dashboard

A Streamlit web application to view and analyze commodity prices in China over the past 5 years. The app fetches real-time and historical data from Chinese commodity exchanges (SHFE and DCE) with prices displayed in RMB.

## Features

- **Interactive Price Charts**: View time-series price data with interactive Plotly charts
- **Multiple Commodities**: Track copper, PVC, aluminum, steel, and zinc prices
- **Price Comparisons**: Compare multiple commodities on the same chart
- **Statistics Panel**: View key metrics including average, min/max prices, volatility, and percentage changes
- **Trend Analysis**: Moving averages and trend indicators
- **Data Caching**: Local caching to improve performance and reduce API calls
- **RMB Pricing**: All prices displayed in Chinese Yuan (RMB)

## Supported Commodities

- **Copper (cu)** - Shanghai Futures Exchange (SHFE)
- **Aluminum (al)** - Shanghai Futures Exchange (SHFE)
- **Zinc (zn)** - Shanghai Futures Exchange (SHFE)
- **Steel/Rebar (rb)** - Shanghai Futures Exchange (SHFE)
- **PVC (v)** - Dalian Commodity Exchange (DCE)

## Installation

1. Clone or download this repository

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit application:
```bash
streamlit run app.py
```

2. The app will open in your default web browser

3. Use the sidebar to:
   - Select commodities to display
   - Choose date range (default: last 5 years)
   - Toggle statistics and trend analysis
   - Adjust moving average period

4. View interactive charts, statistics, and trend analysis in the main panel

## Data Source

This application uses the [akshare](https://github.com/akfamily/akshare) library to fetch commodity futures data from:
- **Shanghai Futures Exchange (SHFE)**: For metals (copper, aluminum, zinc, steel)
- **Dalian Commodity Exchange (DCE)**: For PVC

All prices are in RMB (Chinese Yuan) as provided by the exchanges.

## Data Caching

The application caches fetched data locally in the `data_cache/` directory to:
- Reduce API calls
- Improve load times
- Work offline with previously fetched data

Cache files are automatically created and reused when the same commodity and date range are requested.

## Requirements

- Python 3.7+
- streamlit >= 1.28.0
- pandas >= 2.0.0
- plotly >= 5.17.0
- akshare >= 1.11.0
- requests >= 2.31.0

## Notes

- Internet connection required for initial data fetching
- Data availability depends on akshare library and exchange data availability
- Some historical data may have limitations based on exchange records
- The app handles API rate limits and errors gracefully

## License

This project is provided as-is for educational and informational purposes.

