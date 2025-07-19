import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import datetime

st.title("S&P 500 Stock Screener")

@st.cache_data(show_spinner=False)
def get_sp500_symbols():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    return tables[0]['Symbol'].tolist()

@st.cache_data(show_spinner=False)
def fetch_data(symbol):
    try:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)
        if df.empty or len(df) < 60:
            return None
        df.dropna(inplace=True)

        # Add indicators
        df['ema_13'] = ta.trend.EMAIndicator(df['Close'], window=13).ema_indicator()
        df['ema_48'] = ta.trend.EMAIndicator(df['Close'], window=48).ema_indicator()
        df['ema_200'] = ta.trend.EMAIndicator(df['Close'], window=200).ema_indicator()
        df['rsi'] = ta.momentum.RSIIndicator(df['Close']).rsi()
        return df
    except Exception:
        return None

def analyze_stock(symbol, df):
    score = 0
    details = []

    if df is None or len(df) < 50:
        return None

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # 13 EMA crosses above 48 EMA
    if prev['ema_13'] < prev['ema_48'] and latest['ema_13'] > latest['ema_48']:
        score += 1
        details.append("13 EMA crossed above 48 EMA")

    # Price below 200 EMA
    if latest['Close'] < latest['ema_200']:
        score += 1
        details.append("Price below 200 EMA")

    # RSI above 35
    if latest['rsi'] > 35:
        score += 1
        details.append("RSI > 35")

    if score >= 2:
        return {
            "Symbol": symbol,
            "Score": score,
            "Criteria Met": ", ".join(details),
            "Price": round(latest['Close'], 2),
            "RSI": round(latest['rsi'], 2)
        }
    else:
        return None

st.write("Scanning the S&P 500 for stocks meeting at least 2 of 3 conditions...")

symbols = get_sp500_symbols()
results = []

for symbol in symbols:
    df = fetch_data(symbol)
    result = analyze_stock(symbol, df)
    if result:
        results.append(result)

if results:
    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values(by="Score", ascending=False)
    st.dataframe(df_results)
else:
    st.write("No stocks met 2 or more criteria.")
