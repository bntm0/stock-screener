import streamlit as st
import yfinance as yf
import pandas as pd
import ta

st.title("S&P 500 + NASDAQ-100 EMA Crossover Screener (Last 5 Days)")

@st.cache_data(show_spinner=False)
def get_sp500_symbols():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    return tables[0]['Symbol'].tolist()

@st.cache_data(show_spinner=False)
def get_nasdaq100_symbols():
    url = "https://en.wikipedia.org/wiki/NASDAQ-100"
    tables = pd.read_html(url)
    df = tables[4] if 'Ticker' in tables[4].columns else tables[3]
    return df['Ticker'].str.replace(r"\.", "-", regex=True).tolist()

@st.cache_data(show_spinner=False)
def fetch_data(symbol):
    try:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)
        if df.empty or len(df) < 60:
            return None
        df['ema_13'] = ta.trend.EMAIndicator(df['Close'], window=13).ema_indicator()
        df['ema_48'] = ta.trend.EMAIndicator(df['Close'], window=48).ema_indicator()
        df.dropna(inplace=True)
        return df
    except Exception:
        return None

def crossed_within_last_n_days(df, n=100):
    ema_13 = df['ema_13']
    ema_48 = df['ema_48']

    for i in range(-n, -1):
        if ema_13.iloc[i] < ema_48.iloc[i] and ema_13.iloc[i + 1] > ema_48.iloc[i + 1]:
            return True
    return False

def analyze_stock(symbol, df):
    if df is None or len(df) < 50:
        return None

    if crossed_within_last_n_days(df, n=5):
        latest = df.iloc[-1]
        return {
            "Symbol": symbol,
            "Price": round(latest['Close'], 2),
            "13 EMA": round(latest['ema_13'], 2),
            "48 EMA": round(latest['ema_48'], 2)
        }
    return None

st.write("Scanning **S&P 500 + NASDAQ-100** stocks where **13 EMA crossed above 48 EMA in the last 5 trading days**...")

symbols_sp = get_sp500_symbols()
symbols_nq = get_nasdaq100_symbols()
all_symbols = list(set(symbols_sp + symbols_nq))

results = []
for symbol in all_symbols:
    df = fetch_data(symbol)
    result = analyze_stock(symbol, df)
    if result:
        results.append(result)

if results:
    st.success(f"{len(results)} stocks matched the EMA crossover condition.")
    st.dataframe(pd.DataFrame(results))
else:
    st.warning("No stocks matched the EMA crossover condition.")
