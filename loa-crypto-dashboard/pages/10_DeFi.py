import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.api_client import get_tvl, get_apy, get_gas_price, get_prices
from utils.theme_manager import get_theme, apply_theme

st.set_page_config(page_title="DeFi | LOA-CryptoHub", page_icon="🌐", layout="wide")

theme = get_theme(st.session_state.get("theme_name", "Тёмная"))
apply_theme(theme)

if st.session_state.get("user") is None:
    st.warning("⚠️ Пожалуйста, войдите через VK ID на главной странице.")
    st.stop()

user = st.session_state.user
user_id = user.get("user_id", "")

st.markdown(f"<h1 style='color:{theme['accent1']}'>🌐 DeFi-аналитика</h1>", unsafe_allow_html=True)
st.caption(f"Пользователь: {user.get('username', user_id)} | Данные кэшируются на 2 минуты")

tab_tvl, tab_apy, tab_gas = st.tabs(["📊 TVL", "💰 APY", "⛽ Газ"])

# ------------------------------------------------------------------
with tab_tvl:
    st.subheader("Total Value Locked (TVL)")

    with st.spinner("Загрузка данных TVL..."):
        tvl_data, tvl_ok = get_tvl()

    if not tvl_ok:
        st.warning("⚠️ Эндпоинт `/api/v1/defi/tvl` недоступен или в разработке.")

    if tvl_data:
        total_tvl = None
        protocols = []

        if isinstance(tvl_data, dict):
            total_tvl = tvl_data.get("total_tvl", tvl_data.get("tvl", tvl_data.get("total", None)))
            protocols = tvl_data.get("protocols", tvl_data.get("data", []))
        elif isinstance(tvl_data, list):
            protocols = tvl_data

        if total_tvl is not None:
            st.metric("🌐 Общий TVL (USD)", f"${float(total_tvl):,.0f}")
            st.markdown("---")

        if protocols:
            df_proto = pd.DataFrame(protocols)
            tvl_col = next((c for c in ("tvl", "tvl_usd", "value") if c in df_proto.columns), None)
            name_col = next((c for c in ("name", "protocol", "symbol") if c in df_proto.columns), None)

            if tvl_col and name_col:
                df_proto = df_proto.sort_values(tvl_col, ascending=False).head(10)

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Топ-10 протоколов")
                    display = df_proto[[name_col, tvl_col]].copy()
                    display.columns = ["Протокол", "TVL (USD)"]
                    display["TVL (USD)"] = display["TVL (USD)"].apply(lambda x: f"${float(x):,.0f}" if x else "N/A")
                    st.dataframe(display, use_container_width=True, hide_index=True)
                with col2:
                    fig = px.bar(
                        df_proto,
                        x=name_col,
                        y=tvl_col,
                        title="TVL по протоколам",
                        color=tvl_col,
                        color_continuous_scale=["#1e3a5f", theme["accent1"]],
                    )
                    fig.update_layout(
                        plot_bgcolor=theme["card_bg"],
                        paper_bgcolor=theme["bg"],
                        font_color=theme["text"],
                        showlegend=False,
                        coloraxis_showscale=False,
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.json(protocols[:10])
        else:
            st.info("Данные по протоколам отсутствуют.")
    else:
        st.info("⚙️ Данные TVL будут доступны после запуска эндпоинта `/api/v1/defi/tvl` на API.")

# ------------------------------------------------------------------
with tab_apy:
    st.subheader("APY — годовая доходность")

    prices, _ = get_prices()
    symbols = [p["symbol"] for p in prices] if prices else []
    common_tokens = ["USDT", "USDC", "ETH", "BTC", "BNB", "DAI", "BUSD"]
    default_symbols = [s for s in common_tokens if s in symbols] or symbols[:7] if symbols else common_tokens

    col_search, col_btn = st.columns([3, 1])
    with col_search:
        apy_symbol = st.selectbox("Выберите токен", default_symbols + [s for s in symbols if s not in default_symbols]) if symbols else st.text_input("Тикер токена", value="USDT")
    with col_btn:
        st.markdown("<br/>", unsafe_allow_html=True)
        search_apy = st.button("Найти APY", use_container_width=True)

    if search_apy or apy_symbol:
        with st.spinner(f"Поиск APY для {apy_symbol}..."):
            apy_data, apy_ok = get_apy(apy_symbol)

        if apy_ok and apy_data:
            if isinstance(apy_data, list):
                pools = apy_data
            elif isinstance(apy_data, dict):
                pools = apy_data.get("pools", apy_data.get("data", [apy_data]))
            else:
                pools = []

            if pools:
                st.success(f"Найдено {len(pools)} пул(ов) для {apy_symbol}")
                df_apy = pd.DataFrame(pools)
                st.dataframe(df_apy, use_container_width=True, hide_index=True)
            else:
                raw_apy = apy_data.get("apy", apy_data.get("rate", None)) if isinstance(apy_data, dict) else None
                if raw_apy is not None:
                    st.metric(f"APY для {apy_symbol}", f"{float(raw_apy):.2f}%")
                else:
                    st.json(apy_data)
        else:
            st.warning(f"⚙️ APY для {apy_symbol} недоступен. Эндпоинт `/api/v1/defi/apy/{'{symbol}'}` в разработке.")

# ------------------------------------------------------------------
with tab_gas:
    st.subheader("⛽ Цена газа")

    with st.spinner("Загрузка данных о газе..."):
        gas_data, gas_ok = get_gas_price()

    if not gas_ok:
        st.warning("⚠️ Эндпоинт `/api/v1/defi/gas` недоступен или в разработке.")

    if gas_data:
        if isinstance(gas_data, dict):
            networks = []
            for key, val in gas_data.items():
                if isinstance(val, dict):
                    networks.append({
                        "network": key,
                        "slow":     val.get("slow", val.get("low", "—")),
                        "average":  val.get("average", val.get("standard", "—")),
                        "fast":     val.get("fast", val.get("high", "—")),
                        "unit":     val.get("unit", "Gwei"),
                    })
                elif isinstance(val, (int, float)):
                    networks.append({"network": key, "average": val, "unit": "Gwei"})

            if networks:
                net_cols = st.columns(min(len(networks), 4))
                for i, net in enumerate(networks):
                    with net_cols[i % 4]:
                        st.markdown(
                            f"""
                            <div class="metric-card" style="text-align:center">
                                <div style="font-weight:bold;color:{theme['accent1']};font-size:1.1em">{net['network'].upper()}</div>
                                <div style="margin-top:8px">
                                    <div style="color:{theme['positive']}">🐢 Медленно: <strong>{net.get('slow','—')}</strong></div>
                                    <div style="color:{theme['accent2']}">🚶 Обычно: <strong>{net.get('average','—')}</strong></div>
                                    <div style="color:{theme['negative']}">🚀 Быстро: <strong>{net.get('fast','—')}</strong></div>
                                    <div style="color:{theme['subtext']};font-size:0.8em">{net.get('unit','Gwei')}</div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
            else:
                st.json(gas_data)
        else:
            st.write(gas_data)

        if st.button("🔄 Обновить данные о газе", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    else:
        st.info("⚙️ Данные о цене газа будут доступны после запуска эндпоинта `/api/v1/defi/gas`.")
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="font-weight:bold;color:{theme['text']}">Что такое Gas Price?</div>
                <p style="color:{theme['subtext']}">
                    Gas Price — стоимость одной единицы вычислений в блокчейне (в Gwei для Ethereum).
                    Чем выше газ, тем быстрее обработается транзакция. Рекомендуется проверять перед крупными сделками.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
