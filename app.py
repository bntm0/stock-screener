import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="S&P 500 Stock Screener", layout="wide")
st.title("📈 S&P 500 Stock Screener")

@st.cache_data(show_spinner=False)
def get_sp500_symbols():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    df = tables[0]
    return df['Symbol'].tolist()

symbols = get_sp500_symbols()

@st.cache_data(show_spinner=False)
def fetch_data(symbol):
    try:
        df = yf.download(symbol, period='6mo', interval='1d', progress=False)
        if df.empty or len(df) < 50:
            return None

        df.dropna(inplace=True)

        # Indicators
        df['rsi'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        macd = ta.trend.MACD(df['Close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_hist'] = macd.macd_diff()
        df['ema_200'] = ta.trend.EMAIndicator(df['Close'], window=200).ema_indicator()
        df['ema_13'] = ta.trend.EMAIndicator(df['Close'], window=13).ema_in]()
