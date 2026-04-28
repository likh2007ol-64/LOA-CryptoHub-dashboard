import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.api_client import get_prices, get_portfolio, add_portfolio_item, delete_portfolio_item
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
        total_value = 0
        factor = 1 + random.uniform(-0.02, 0.02)
        for item in portfolio:
            symbol = item.get("symbol", "")
            current_price = price_map.get(symbol, 0)
            hist_price = current_price * (0.85 + random.uniform(0, 0.3)) * factor
            total_value += item.get("amount", 0) * hist_price
        records.append({"date": date.strftime("%Y-%m-%d"), "value": round(total_value, 2)})
    return pd.DataFrame(records)


prices, prices_ok = get_prices()
if not prices_ok or not prices:
    st.warning("⚠️ Не удалось загрузить курсы с API. Отображение P&L недоступно.")

price_map = {p["symbol"]: p["price"] for p in prices} if prices else {}

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
            "symbol": symbol,
            "amount": amount,
            "avg_buy_price": avg_buy,
            "current_price": current_price,
            "value": value,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
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
        pie_data = pd.DataFrame(enriched)
        fig_pie = px.pie(
            pie_data,
            values="value",
            names="symbol",
            color_discrete_sequence=px.colors.qualitative.Set2,
            title="По стоимости",
        )
        fig_pie.update_layout(
            plot_bgcolor=theme["card_bg"],
            paper_bgcolor=theme["bg"],
            font_color=theme["text"],
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_chart2:
        st.subheader("P&L по монетам")
        pnl_df = pd.DataFrame(enriched)
        fig_pnl = px.bar(
            pnl_df,
            x="symbol",
            y="pnl",
            color="pnl",
            color_continuous_scale=["#FF6B6B", "#888888", "#00F0A0"],
            color_continuous_midpoint=0,
            labels={"symbol": "Монета", "pnl": "P&L ($)"},
            title="Прибыль/убыток по монетам ($)",
        )
        fig_pnl.update_layout(
            plot_bgcolor=theme["card_bg"],
            paper_bgcolor=theme["bg"],
            font_color=theme["text"],
            showlegend=False,
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_pnl, use_container_width=True)

    if price_map:
        st.subheader("📈 Динамика стоимости портфеля (30 дней)")
        history_df = _generate_portfolio_history(portfolio, price_map)
        fig_hist = px.area(
            history_df,
            x="date",
            y="value",
            labels={"date": "Дата", "value": "Стоимость ($)"},
            color_discrete_sequence=[theme["accent1"]],
        )
        fig_hist.update_layout(
            plot_bgcolor=theme["card_bg"],
            paper_bgcolor=theme["bg"],
            font_color=theme["text"],
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("---")
    st.subheader("Состав портфеля")

    for item in enriched:
        symbol = item["symbol"]
        pnl_sign = "+" if item["pnl"] >= 0 else ""
        pnl_color = theme["positive"] if item["pnl"] >= 0 else theme["negative"]
        price_str = f"${item['current_price']:,.4f}" if item["current_price"] < 1 else f"${item['current_price']:,.2f}"
        buy_str = f"${item['avg_buy_price']:,.4f}" if item["avg_buy_price"] < 1 else f"${item['avg_buy_price']:,.2f}"

        col_info, col_del = st.columns([6, 1])
        with col_info:
            st.markdown(
                f"""
                <div class="metric-card">
                    <strong style="color:{theme['accent1']};font-size:1.1em">{symbol}</strong>
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
                    st.success(f"✅ {symbol} удалён из портфеля")
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
        default_price = price_map.get(new_symbol, 0.0) if prices and new_symbol else 0.0
        new_price = st.number_input("Цена покупки ($)", min_value=0.0001, value=float(default_price) or 1.0, step=0.01, format="%.4f")
    submitted = st.form_submit_button("Добавить", use_container_width=True)
    if submitted and new_symbol:
        ok = add_portfolio_item(user_id, new_symbol, new_amount, new_price)
        if ok:
            st.success(f"✅ {new_symbol} добавлен в портфель!")
            st.rerun()
        else:
            st.error(f"❌ Не удалось добавить {new_symbol}. Проверьте подключение к API.")
