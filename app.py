import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="Stock Screener", layout="wide")
st.title("📈 S&P 500 Technical Stock Screener")

st.markdown("""
This screener scans **all S&P 500 stocks** using these technical criteria on daily data:

- RSI crossing 50 from below
- MACD rising but still below zero (last 5 days)
- Price below 200-day EMA
- 13-day EMA recently crossed above 48-day EMA

Use the slider to filter stocks by minimum criteria met for the main table.
Stocks meeting exactly 2 or 3 criteria are shown in a separate table.
""")

@st.cache_data(show_spinner=False)
def get_sp500_symbols():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    symbols = tables[0]['Symbol'].tolist()
    # Fix for tickers with dots (Yahoo uses -)
    symbols = [sym.replace('.', '-') for sym in symbols]
    return symbols

symbols = get_sp500_symbols()
st.write(f"Loaded {len(symbols)} S&P 500 symbols.")

min_criteria = st.slider("Minimum number of criteria met (for main table)", 1, 4, 4)

@st.cache_data(show_spinner=False)
def fetch_data(symbol):
    try:
        df = yf.download(symbol, period='6mo', interval='1d', progress=False)
        if df.shape[0] < 50:
            return None

        df['rsi'] = ta.momentum.RSIIndicator(df['Close']).rsi()
        macd = ta.trend.MACD(df['Close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['ema_200'] = ta.trend.EMAIndicator(df['Close'], window=200).ema_indicator()
        df['ema_13'] = ta.trend.EMAIndicator(df['Close'], window=13).ema_indicator()
        df['ema_48'] = ta.trend.EMAIndicator(df['Close'], window=48).ema_indicator()
