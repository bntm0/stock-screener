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

Use the slider to filter stocks by minimum criteria met.
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

min_criteria = st.slider("Minimum number of criteria met", 1, 4, 3)

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

        df.dropna(inplace=True)
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Criteria 1: RSI crossing 50 from below
        rsi_cross = prev['rsi'] < 50 and last['rsi'] >= 50

        # Criteria 2: MACD rising last 5 days and still below 0
        macd_diff = df['macd'].diff()
        macd_up = all(macd_diff.iloc[-5:] > 0) and last['macd'] < 0

        # Criteria 3: Price below 200 EMA
        below_200ema = last['Close'] < last['ema_200']

        # Criteria 4: 13 EMA crossed above 48 EMA recently (last 3 bars)
        ema_cross = False
        for i in range(-4, -1):
            if df['ema_13'].iloc[i] < df['ema_48'].iloc[i] and df['ema_13'].iloc[i+1] > df['ema_48'].iloc[i+1]:
                ema_cross = True
                break

        criteria_list = [rsi_cross, macd_up, below_200ema, ema_cross]
        criteria_met = sum(criteria_list)

        if criteria_met < min_criteria:
            return None

        return {
            'Symbol': symbol,
            'Price': round(last['Close'], 2),
            'RSI Cross': rsi_cross,
            'MACD Rising': macd_up,
            '<200 EMA': below_200ema,
            '13/48 EMA Cross': ema_cross,
            'Criteria Met': criteria_met
        }

    except Exception:
        return None

with st.spinner("Scanning stocks, please wait..."):
    with ThreadPoolExecutor(max_workers=15) as executor:
        results = list(executor.map(fetch_data, symbols))

    results = [res for res in results if res is not None]

if results:
    df = pd.DataFrame(results)
    df.sort_values(by='Criteria Met', ascending=False, inplace=True)

    def emoji_bool(x):
        return "✅" if x else "❌"

    for col in ['RSI Cross', 'MACD Rising', '<200 EMA', '13/48 EMA Cross']:
        df[col] = df[col].apply(emoji_bool)

    st.success(f"Found {len(df)} stocks meeting at least {min_criteria} criteria.")

    st.dataframe(df.reset_index(drop=True), use_container_width=True)

    csv = df.to_csv(index=False)
    st.download_button("Download CSV", csv, "stock_screener_results.csv", "text/csv")

else:
    st.warning("No stocks matched the criteria.")
