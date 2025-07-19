import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import datetime

st.title("S&P 500 Technical Stock Screener")

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

        df['rsi'] = ta.momentum.RSIIndicator(df['Close']).rsi()
        macd = ta.trend.MACD(df['Close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['ema_200'] = ta.trend.EMAIndicator(df['Close'], window=200).ema_indicator()
        df['ema_13'] = ta.trend.EMAIndicator(df['Close'], window=13).ema_indicator()
        df['ema_48'] = ta.trend.EMAIndicator(df['Close'], window=48).ema_indicator()
        return df
    except Exception:
        return None

def analyze_stock(symbol, df):
    score = 0
    details = []

    if df is None or len(df) < 50:
        return None

    latest = df.iloc[-1]
    prev_rsi = df['rsi'].iloc[-2]
    curr_rsi = latest['rsi']
    if prev_rsi < 50 and curr_rsi > 50:
        score += 1
        details.append("RSI crossed 50 from below")

    recent_macds = df['macd'].tail(5)
    if all(recent_macds.diff().dropna() > 0) and recent_macds.iloc[-1] < 0:
        score += 1
        details.append("MACD rising for 5 days, still below 0")

    if latest['Close'] < latest['ema_200']:
        score += 1
        details.append("Price below 200 EMA")

    prev_13 = df['ema_13'].iloc[-2]
    prev_48 = df['ema_48'].iloc[-2]
    curr_13 = latest['ema_13']
    curr_48 = latest['ema_48']
    if prev_13 < prev_48 and curr_13 > curr_48:
        score += 1
        details.append("13 EMA crossed above 48 EMA")

    if score >= 2:
        return {
            "Symbol": symbol,
            "Score": score,
            "Criteria Met": ", ".join(details),
            "Price": round(latest['Close'], 2),
            "RSI": round(curr_rsi, 2),
            "MACD": round(latest['macd'], 3)
        }
    else:
        return None

st.write("Screening stocks from the S&P 500...")

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
