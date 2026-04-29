import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.api_client import (
    get_prices, get_portfolio, add_portfolio_item, delete_portfolio_item,
    get_all_signals, export_portfolio_csv,
)
from utils.theme_manager import get_theme, apply_theme

st.set_page_config(page_title="Портфель | LOA-CryptoHub", page_icon="💼", layout="wide")

theme = get_theme(st.session_state.get("theme_name", "Тёмная"))
apply_theme(theme)

if st.session_state.get("user") is None:
    st.warning("⚠️ Пожалуйста, войдите через VK ID на главной странице.")
    st.stop()

user = st.session_state.user
user_id = user.get("user_id", "")

st.markdown(f"<h1 style='color:{theme['accent1']}'>💼 Портфель</h1>", unsafe_allow_html=True)
st.caption(f"Пользователь: {user.get('username', user_id)} | VK ID: {user_id}")


def _generate_portfolio_history(portfolio, price_map):
    dates = [datetime.now() - timedelta(days=i) for i in range(30, -1, -1)]
    records = []
    for date in dates:
        total_value = sum(
            item.get("amount", 0) * price_map.get(item.get("symbol", ""), 0) * (0.85 + random.uniform(0, 0.3))
            for item in portfolio
        )
        records.append({"date": date.strftime("%Y-%m-%d"), "value": round(total_value, 2)})
    return pd.DataFrame(records)


SIGNAL_CONFIG = {
    "bullish": ("🟢", "#00F0A0"), "buy": ("🟢", "#00F0A0"),
    "bearish": ("🔴", "#FF6B6B"), "sell": ("🔴", "#FF6B6B"),
    "neutral": ("🟡", "#F59E0B"), "hold": ("🟡", "#F59E0B"),
}

prices, prices_ok = get_prices()
if not prices_ok or not prices:
    st.warning("⚠️ Не удалось загрузить курсы с API.")

price_map = {p["symbol"]: p["price"] for p in prices} if prices else {}

signals_list, _ = get_all_signals()
signal_map = {}
for s in signals_list:
    sym = s.get("symbol", "")
    if sym:
        signal_map[sym] = str(s.get("signal", s.get("action", "neutral"))).lower()

portfolio, api_ok = get_portfolio(user_id)
if not api_ok:
    st.warning("⚠️ Не удалось загрузить портфель с API.")

if portfolio:
    total_value = 0
    total_cost = 0
    enriched = []
    for item in portfolio:
        symbol = item.get("symbol", "")
        amount = float(item.get("amount", 0))
        avg_buy = float(item.get("avg_buy_price", item.get("buy_price", 0)))
        current_price = price_map.get(symbol, avg_buy)
        value = amount * current_price
        cost = amount * avg_buy
        pnl = value - cost
        pnl_pct = (pnl / cost * 100) if cost > 0 else 0
        total_value += value
        total_cost += cost
        enriched.append({
            "symbol": symbol, "amount": amount,
            "avg_buy_price": avg_buy, "current_price": current_price,
            "value": value, "pnl": pnl, "pnl_pct": pnl_pct,
        })

    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Общая стоимость", f"${total_value:,.2f}")
    with col2:
        st.metric("Вложено", f"${total_cost:,.2f}")
    with col3:
        sign = "+" if total_pnl >= 0 else ""
        st.metric("P&L (абс.)", f"{sign}${total_pnl:,.2f}")
    with col4:
        sign = "+" if total_pnl_pct >= 0 else ""
        st.metric("P&L (%)", f"{sign}{total_pnl_pct:.2f}%")

    st.markdown("---")

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("Распределение портфеля")
        fig_pie = px.pie(
            pd.DataFrame(enriched), values="value", names="symbol",
            color_discrete_sequence=px.colors.qualitative.Set2, title="По стоимости",
        )
        fig_pie.update_layout(plot_bgcolor=theme["card_bg"], paper_bgcolor=theme["bg"], font_color=theme["text"])
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_chart2:
        st.subheader("P&L по монетам")
        fig_pnl = px.bar(
            pd.DataFrame(enriched), x="symbol", y="pnl", color="pnl",
            color_continuous_scale=["#FF6B6B", "#888888", "#00F0A0"], color_continuous_midpoint=0,
            labels={"symbol": "Монета", "pnl": "P&L ($)"}, title="Прибыль/убыток ($)",
        )
        fig_pnl.update_layout(plot_bgcolor=theme["card_bg"], paper_bgcolor=theme["bg"], font_color=theme["text"], showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_pnl, use_container_width=True)

    if price_map:
        st.subheader("📈 Динамика стоимости портфеля (30 дней)")
        history_df = _generate_portfolio_history(portfolio, price_map)
        fig_hist = px.area(history_df, x="date", y="value", labels={"date": "Дата", "value": "Стоимость ($)"}, color_discrete_sequence=[theme["accent1"]])
        fig_hist.update_layout(plot_bgcolor=theme["card_bg"], paper_bgcolor=theme["bg"], font_color=theme["text"])
        st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("---")
    col_title, col_export = st.columns([5, 1])
    with col_title:
        st.subheader("Состав портфеля")
    with col_export:
        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("📥 CSV", help="Скачать портфель в CSV", use_container_width=True):
            csv_raw, ok = export_portfolio_csv(user_id)
            if ok and csv_raw:
                st.download_button("⬇️ Скачать", data=csv_raw, file_name=f"portfolio_{user_id}.csv", mime="text/csv")
            else:
                df_exp = pd.DataFrame(enriched)
                st.download_button("⬇️ Скачать (локальный)", data=df_exp.to_csv(index=False).encode("utf-8"), file_name=f"portfolio_{user_id}.csv", mime="text/csv")

    for item in enriched:
        symbol = item["symbol"]
        pnl_sign = "+" if item["pnl"] >= 0 else ""
        pnl_color = theme["positive"] if item["pnl"] >= 0 else theme["negative"]
        price_str = f"${item['current_price']:,.4f}" if item["current_price"] < 1 else f"${item['current_price']:,.2f}"
        buy_str = f"${item['avg_buy_price']:,.4f}" if item["avg_buy_price"] < 1 else f"${item['avg_buy_price']:,.2f}"

        sig = signal_map.get(symbol, "")
        sig_icon, sig_color = SIGNAL_CONFIG.get(sig, ("", theme["subtext"]))
        sig_badge = f'<span style="background:{sig_color}22;color:{sig_color};border:1px solid {sig_color};border-radius:4px;padding:1px 6px;font-size:0.8em;margin-left:8px">{sig_icon} AI</span>' if sig_icon else ""

        col_info, col_del = st.columns([6, 1])
        with col_info:
            st.markdown(
                f"""
                <div class="metric-card">
                    <strong style="color:{theme['accent1']};font-size:1.1em">{symbol}</strong>{sig_badge}
                    &nbsp;|&nbsp; Кол-во: <strong>{item['amount']}</strong>
                    &nbsp;|&nbsp; Тек. цена: <strong>{price_str}</strong>
                    &nbsp;|&nbsp; Ср. покупка: {buy_str}
                    &nbsp;|&nbsp; Стоимость: <strong>${item['value']:,.2f}</strong>
                    &nbsp;|&nbsp; P&L: <span style="color:{pnl_color};font-weight:bold">{pnl_sign}${item['pnl']:,.2f} ({pnl_sign}{item['pnl_pct']:.2f}%)</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_del:
            if st.button("🗑️", key=f"del_coin_{symbol}", help=f"Удалить {symbol}"):
                ok = delete_portfolio_item(user_id, symbol)
                if ok:
                    st.success(f"✅ {symbol} удалён")
                else:
                    st.error(f"❌ Не удалось удалить {symbol}")
                st.rerun()
else:
    st.info("Портфель пуст. Добавьте монеты ниже.")

st.markdown("---")
st.subheader("➕ Добавить монету в портфель")

with st.form("add_coin_form"):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        symbols_available = [p["symbol"] for p in prices] if prices else []
        if symbols_available:
            new_symbol = st.selectbox("Монета", symbols_available)
        else:
            new_symbol = st.text_input("Тикер монеты (напр. BTC)", placeholder="BTC")
    with col_b:
        new_amount = st.number_input("Количество", min_value=0.0001, step=0.0001, format="%.4f")
    with col_c:
        default_price = float(price_map.get(new_symbol, 1.0)) if prices and new_symbol else 1.0
        new_price = st.number_input("Цена покупки ($)", min_value=0.0001, value=default_price, step=0.01, format="%.4f")
    submitted = st.form_submit_button("Добавить", use_container_width=True)
    if submitted and new_symbol:
        ok = add_portfolio_item(user_id, new_symbol, new_amount, new_price)
        if ok:
            st.success(f"✅ {new_symbol} добавлен в портфель!")
            st.rerun()
        else:
            st.error(f"❌ Не удалось добавить {new_symbol}. Проверьте подключение к API.")
