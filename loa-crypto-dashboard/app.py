import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from utils.api_client import get_prices, get_user
from utils.theme_manager import get_theme, apply_theme, THEMES

st.set_page_config(
    page_title="LOA-CryptoHub Dashboard",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "user" not in st.session_state:
    st.session_state.user = None
if "theme_name" not in st.session_state:
    st.session_state.theme_name = "Тёмная"
if "api_live" not in st.session_state:
    st.session_state.api_live = False

theme = get_theme(st.session_state.theme_name)
apply_theme(theme)

with st.sidebar:
    st.markdown(f"<h2 style='color:{theme['accent1']}'>🔐 LOA-CryptoHub</h2>", unsafe_allow_html=True)
    st.markdown("---")

    st.subheader("Тема оформления")
    selected_theme = st.selectbox(
        "Выберите тему",
        list(THEMES.keys()),
        index=list(THEMES.keys()).index(st.session_state.theme_name),
        label_visibility="collapsed",
    )
    if selected_theme != st.session_state.theme_name:
        st.session_state.theme_name = selected_theme
        st.rerun()

    st.markdown("---")
    st.subheader("Вход через VK ID")

    if st.session_state.user is None:
        vk_id_input = st.text_input("VK ID", placeholder="Введите ваш VK ID...", key="vk_id_input")
        if st.button("Войти", use_container_width=True):
            if vk_id_input.strip():
                with st.spinner("Проверка пользователя..."):
                    user_data, api_ok = get_user(vk_id_input.strip())
                    st.session_state.api_live = api_ok
                    if user_data:
                        st.session_state.user = user_data
                        st.success(f"Добро пожаловать, {user_data.get('username', 'Пользователь')}!")
                        st.rerun()
                    else:
                        st.error("Пользователь не найден. Проверьте VK ID.")
            else:
                st.warning("Введите VK ID для входа.")
        st.caption("Тестовые ID: 1 (пользователь), 42 (админ), 100 (эксперт)")
    else:
        user = st.session_state.user
        role_emoji = "👑" if user.get("role") == "admin" else "⭐"
        st.markdown(f"<p style='color:{theme['accent1']}'>{role_emoji} {user.get('username', 'N/A')}</p>", unsafe_allow_html=True)
        st.caption(f"Роль: {user.get('role', 'user')}")
        st.caption(f"Подписка: {user.get('subscription', 'free')}")
        if st.button("Выйти", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    st.markdown("---")
    if not st.session_state.api_live:
        st.markdown(
            "<small style='color:#F5B041'>⚠️ Режим демо (API недоступен)</small>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<small style='color:#00F0A0'>✅ API подключён</small>",
            unsafe_allow_html=True,
        )


st.markdown(f"<h1 style='color:{theme['accent1']}'>🏠 LOA-CryptoHub</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color:{theme['subtext']}'>Платформа криптовалютного мониторинга и управления портфелем</p>", unsafe_allow_html=True)

if st.session_state.user is None:
    st.info("👈 Войдите через VK ID в боковой панели для доступа к полному функционалу.")
    st.markdown("---")

st.subheader("📊 Топ-10 криптовалют в реальном времени")

with st.spinner("Загрузка курсов..."):
    prices, api_ok = get_prices()
    st.session_state.api_live = api_ok

if not api_ok:
    st.caption("⚠️ Используются демо-данные (API недоступен)")

if prices:
    cols = st.columns(5)
    for i, coin in enumerate(prices[:10]):
        with cols[i % 5]:
            change = coin.get("change_24h", 0)
            change_sign = "+" if change >= 0 else ""
            change_color = theme["positive"] if change >= 0 else theme["negative"]
            price = coin.get("price", 0)
            price_str = f"${price:,.2f}" if price >= 1 else f"${price:.4f}"

            st.markdown(
                f"""
                <div class="metric-card">
                    <div style="font-size:1.1em;font-weight:bold;color:{theme['text']}">{coin['symbol']}</div>
                    <div style="color:{theme['subtext']};font-size:0.8em">{coin['name']}</div>
                    <div style="font-size:1.2em;font-weight:bold;color:{theme['accent1']};margin:4px 0">{price_str}</div>
                    <div style="color:{change_color};font-size:0.9em">{change_sign}{change:.2f}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.subheader("📈 Сравнение изменений за 24ч")

    df = pd.DataFrame(prices)
    fig = px.bar(
        df,
        x="symbol",
        y="change_24h",
        color="change_24h",
        color_continuous_scale=["#FF6B6B", "#888888", "#00F0A0"],
        color_continuous_midpoint=0,
        labels={"symbol": "Монета", "change_24h": "Изменение за 24ч (%)"},
        title="Изменение цены за 24 часа (%)",
    )
    fig.update_layout(
        plot_bgcolor=theme["card_bg"],
        paper_bgcolor=theme["bg"],
        font_color=theme["text"],
        showlegend=False,
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🗂️ Полная таблица курсов")
    display_df = pd.DataFrame(prices)[["symbol", "name", "price", "change_24h", "market_cap", "volume_24h"]].copy()
    display_df.columns = ["Символ", "Название", "Цена ($)", "Изм. 24ч (%)", "Капитализация ($)", "Объём 24ч ($)"]
    display_df["Цена ($)"] = display_df["Цена ($)"].apply(lambda x: f"${x:,.4f}" if x < 1 else f"${x:,.2f}")
    display_df["Изм. 24ч (%)"] = display_df["Изм. 24ч (%)"].apply(lambda x: f"+{x:.2f}%" if x >= 0 else f"{x:.2f}%")
    display_df["Капитализация ($)"] = display_df["Капитализация ($)"].apply(lambda x: f"${x/1e9:.1f}B")
    display_df["Объём 24ч ($)"] = display_df["Объём 24ч ($)"].apply(lambda x: f"${x/1e9:.2f}B")
    st.dataframe(display_df, use_container_width=True, hide_index=True)
