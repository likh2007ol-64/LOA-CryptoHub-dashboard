import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.api_client import get_prices, get_portfolio, add_portfolio_item, generate_portfolio_history
from utils.theme_manager import get_theme, apply_theme, THEMES

st.set_page_config(page_title="Портфель | LOA-CryptoHub", page_icon="💼", layout="wide")

theme = get_theme(st.session_state.get("theme_name", "Тёмная"))
apply_theme(theme)

if st.session_state.get("user") is None:
    st.warning("⚠️ Пожалуйста, войдите через VK ID на главной странице.")
    st.stop()

user = st.session_state.user
user_id = user.get("user_id", "1")

st.markdown(f"<h1 style='color:{theme['accent1']}'>💼 Портфель</h1>", unsafe_allow_html=True)
st.caption(f"Пользователь: {user.get('username')} | ID: {user_id}")

prices, _ = get_prices()
portfolio, api_ok = get_portfolio(user_id)

if not api_ok:
    st.caption("⚠️ Используются демо-данные")

price_map = {p["symbol"]: p["price"] for p in prices}

if portfolio:
    total_value = 0
    total_cost = 0
    enriched = []
    for item in portfolio:
        symbol = item.get("symbol", "")
        amount = item.get("amount", 0)
        avg_buy = item.get("avg_buy_price", 0)
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
        color = theme["positive"] if total_pnl >= 0 else theme["negative"]
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

    st.subheader("📈 Динамика стоимости портфеля (30 дней)")
    history_df = generate_portfolio_history(portfolio, prices)
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
    df_display = pd.DataFrame(enriched)
    df_display["current_price"] = df_display["current_price"].apply(lambda x: f"${x:,.4f}" if x < 1 else f"${x:,.2f}")
    df_display["avg_buy_price"] = df_display["avg_buy_price"].apply(lambda x: f"${x:,.4f}" if x < 1 else f"${x:,.2f}")
    df_display["value"] = df_display["value"].apply(lambda x: f"${x:,.2f}")
    df_display["pnl"] = df_display["pnl"].apply(lambda x: f"+${x:,.2f}" if x >= 0 else f"-${abs(x):,.2f}")
    df_display["pnl_pct"] = df_display["pnl_pct"].apply(lambda x: f"+{x:.2f}%" if x >= 0 else f"{x:.2f}%")
    df_display.columns = ["Монета", "Кол-во", "Ср. цена покупки", "Текущая цена", "Стоимость", "P&L ($)", "P&L (%)"]
    st.dataframe(df_display, use_container_width=True, hide_index=True)
else:
    st.info("Портфель пуст.")

st.markdown("---")
st.subheader("➕ Добавить монету в портфель")
with st.form("add_coin_form"):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        symbols_available = [p["symbol"] for p in prices]
        new_symbol = st.selectbox("Монета", symbols_available)
    with col_b:
        new_amount = st.number_input("Количество", min_value=0.0001, step=0.0001, format="%.4f")
    with col_c:
        new_price = st.number_input("Цена покупки ($)", min_value=0.0001, step=0.01, format="%.4f")
    submitted = st.form_submit_button("Добавить", use_container_width=True)
    if submitted:
        ok = add_portfolio_item(user_id, new_symbol, new_amount, new_price)
        if ok:
            st.success(f"✅ {new_symbol} добавлен в портфель!")
            st.rerun()
        else:
            st.info(f"✅ {new_symbol} добавлен (демо-режим — данные не сохраняются на сервере)")
