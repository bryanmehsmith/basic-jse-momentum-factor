"""Interactive Streamlit demo of the JSE 12-1 month momentum factor backtest."""

from datetime import date

import matplotlib.pyplot as plt
import streamlit as st

from momentum_factor.backtest import run_backtest
from momentum_factor.data import get_prices, load_universe
from momentum_factor.performance import summarize
from momentum_factor.signals import momentum_signal

st.set_page_config(page_title="JSE Momentum Factor", layout="wide")


@st.cache_data(ttl=3600, show_spinner="Loading price data...")
def load_prices(tickers: tuple[str, ...], start: str, force_refresh: bool):
    return get_prices(list(tickers), start=start, force_refresh=force_refresh)


universe = load_universe()
all_tickers = universe["ticker"].tolist()

st.title("JSE Momentum Factor Backtest")

with st.sidebar:
    # Root-relative, so it resolves to the demo-site landing page rather than
    # anywhere inside this app's /demos/momentum-factor base path.
    st.markdown("[Back to all demos](/)")
    st.header("Backtest settings")
    quantile = st.slider("Top quantile", min_value=0.05, max_value=0.6, value=0.2, step=0.05)
    formation_months = st.slider("Formation window (months)", min_value=3, max_value=24, value=12, step=1)
    skip_months = st.slider("Skip months", min_value=0, max_value=3, value=1, step=1)
    risk_free_pct = st.number_input(
        "Risk-free rate (% per year)",
        min_value=0.0,
        max_value=20.0,
        value=4.0,
        step=0.25,
        help="Annual rate used as the Sharpe ratio benchmark, converted to monthly.",
    )
    start_date = st.date_input(
        "Start date",
        value=date(2015, 1, 1),
        min_value=date(2010, 1, 1),
        max_value=date.today(),
    )
    selected = st.multiselect("Universe", all_tickers, default=all_tickers)
    use_live = st.checkbox("Try live yfinance refresh (may be rate-limited)", value=False)
    st.caption("Off by default, falls back to a bundled price snapshot if live data is unavailable.")

st.caption(
    f"Momentum factor: rank stocks by trailing {formation_months}-month return "
    f"(skipping the most recent {skip_months} month{'s' if skip_months != 1 else ''}), "
    "hold the top quantile equal-weighted, rebalance monthly."
)

if not selected:
    st.warning("Select at least one ticker in the sidebar.")
    st.stop()

try:
    prices = load_prices(tuple(selected), start_date.isoformat(), use_live)
except Exception as exc:
    st.error(f"Could not load price data: {exc}")
    st.stop()

signal = momentum_signal(prices, formation_months=formation_months, skip_months=skip_months)
returns = run_backtest(prices, signal, quantile=quantile)

if returns.empty:
    st.warning("No backtest periods for this selection, try a wider universe or earlier start date.")
    st.stop()

risk_free_rate = risk_free_pct / 100
stats = summarize(returns, risk_free_rate=risk_free_rate)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Sharpe ratio", f"{stats['sharpe_ratio']:.2f}", help=f"Excess of a {risk_free_pct:.2f}% annual risk-free rate")
col2.metric("Annualized return", f"{stats['annualized_return']:.1%}")
col3.metric("Max drawdown", f"{stats['max_drawdown']:.1%}")
col4.metric("Cumulative return", f"{stats['cumulative_return']:.1%}")

fig, ax = plt.subplots(figsize=(10, 5))
(1 + returns).cumprod().plot(
    ax=ax,
    title=f"Cumulative growth (quantile={quantile}, formation={formation_months}m, skip={skip_months}m)",
)
ax.set_ylabel("Growth of 1")
fig.tight_layout()
st.pyplot(fig)

st.caption(
    "Data: Yahoo Finance via yfinance, with a bundled fallback snapshot if live data "
    "is unavailable. For research/education only, not investment advice."
)
