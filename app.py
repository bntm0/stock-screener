import streamlit as st
import yfinance as yf
import pandas as pd
import ta

st.title("S&P 500 EMA Crossover Screener (Last 100 Days)")

@st.cache_data(show_spinner=False)
def get_sp500_symbols():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    return tables[0]['Symbol'].tolist()

@st.cache_data(show_spinner=False)
def fetch_data(symbol):
    try:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)
        if df.empty or len(df) < 110:  # allow a bit more data for safety
            return None
        df['ema_13'] = ta.trend.EMAIndicator(df['Close'], window=13).ema_indicator()
        df['ema_48'] = ta.trend.EMAIndicator(df['Close'], window=48).ema_indicator()
        df.dropna(inplace=True)
        return df
    except Exception:
        return None

def crossed_within_last_n_days(df, n=100):
    recent = df[-(n+1):].copy()
    recent['ema_above'] = recent['ema_13'] > recent['ema_48']
    # True where crossover happened: today ema_above == True and yesterday ema_above == False
    cross_points = recent['ema_above'] & (~recent['ema_above'].shift(1).fillna(False))
    return cross_points.any()

def analyze_stock(symbol, df):
    if df is None or len(df) < 110:
        return None
    if crossed_within_last_n_days(df, n=100):
        latest = df.iloc[-1]
        return {
            "Symbol": symbol,
            "Price": round(latest['Close'], 2),
            "13 EMA": round(latest['ema_13'], 2),
            "48 EMA": round(latest['ema_48'], 2)
        }
    return None

st.write("Scanning **S&P 500 stocks** where **13 EMA crossed above 48 EMA in the last 100 trading days**...")

symbols_sp = get_sp500_symbols()
results = []

for symbol in symbols_sp:
    df = fetch_data(symbol)
    if df is None:
        st.write(f"Skipping {symbol}: insufficient or no data")
        continue
    result = analyze_stock(symbol, df)
    if result:
        results.append(result)

if results:
    st.success(f"{len(results)} stocks matched the EMA crossover condition.")
    st.dataframe(pd.DataFrame(results))
else:
    st.warning("No stocks matched the EMA crossover condition.")
