import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.api_client import get_transactions
from utils.theme_manager import get_theme, apply_theme

st.set_page_config(page_title="История | LOA-CryptoHub", page_icon="📜", layout="wide")

theme = get_theme(st.session_state.get("theme_name", "Тёмная"))
apply_theme(theme)

if st.session_state.get("user") is None:
    st.warning("⚠️ Пожалуйста, войдите через VK ID на главной странице.")
    st.stop()

user = st.session_state.user
user_id = user.get("user_id", "1")

st.markdown(f"<h1 style='color:{theme['accent1']}'>📜 История транзакций</h1>", unsafe_allow_html=True)
st.caption(f"Пользователь: {user.get('username')} | ID: {user_id}")

transactions, api_ok = get_transactions(user_id)

if not api_ok:
    st.caption("⚠️ Используются демо-данные")

if transactions:
    df = pd.DataFrame(transactions)

    col1, col2, col3 = st.columns(3)
    buy_total = sum(t.get("total", 0) for t in transactions if t.get("type") == "buy")
    sell_total = sum(t.get("total", 0) for t in transactions if t.get("type") == "sell")
    net = sell_total - buy_total
    with col1:
        st.metric("Всего куплено", f"${buy_total:,.2f}")
    with col2:
        st.metric("Всего продано", f"${sell_total:,.2f}")
    with col3:
        st.metric("Чистый результат", f"${net:,.2f}")

    st.markdown("---")

    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        type_filter = st.selectbox("Тип операции", ["Все", "buy", "sell"])
    with col_filter2:
        symbol_filter = st.selectbox("Монета", ["Все"] + list(df["symbol"].unique()))

    filtered = df.copy()
    if type_filter != "Все":
        filtered = filtered[filtered["type"] == type_filter]
    if symbol_filter != "Все":
        filtered = filtered[filtered["symbol"] == symbol_filter]

    st.subheader(f"Транзакции ({len(filtered)})")

    display_df = filtered[["date", "type", "symbol", "amount", "price", "total"]].copy()
    display_df["type"] = display_df["type"].apply(lambda x: "🟢 Покупка" if x == "buy" else "🔴 Продажа")
    display_df["price"] = display_df["price"].apply(lambda x: f"${x:,.2f}")
    display_df["total"] = display_df["total"].apply(lambda x: f"${x:,.2f}")
    display_df.columns = ["Дата", "Тип", "Монета", "Количество", "Цена", "Итого"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📊 Объём операций по монетам")
    vol_df = df.groupby(["symbol", "type"])["total"].sum().reset_index()
    fig = px.bar(
        vol_df,
        x="symbol",
        y="total",
        color="type",
        barmode="group",
        labels={"symbol": "Монета", "total": "Сумма ($)", "type": "Тип"},
        color_discrete_map={"buy": theme["positive"], "sell": theme["negative"]},
        title="Объём операций по монетам",
    )
    fig.update_layout(
        plot_bgcolor=theme["card_bg"],
        paper_bgcolor=theme["bg"],
        font_color=theme["text"],
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("История транзакций пуста.")
