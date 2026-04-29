import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.api_client import get_all_signals, get_signal, get_prices
from utils.theme_manager import get_theme, apply_theme

st.set_page_config(page_title="AI-сигналы | LOA-CryptoHub", page_icon="🤖", layout="wide")

theme = get_theme(st.session_state.get("theme_name", "Тёмная"))
apply_theme(theme)

if st.session_state.get("user") is None:
    st.warning("⚠️ Пожалуйста, войдите через VK ID на главной странице.")
    st.stop()

user = st.session_state.user
user_id = user.get("user_id", "")

st.markdown(f"<h1 style='color:{theme['accent1']}'>🤖 AI-сигналы</h1>", unsafe_allow_html=True)
st.caption(f"Пользователь: {user.get('username', user_id)} | Данные обновляются каждые 60 сек.")

SIGNAL_CONFIG = {
    "bullish":  {"icon": "🟢", "label": "Бычий",     "color": "#00F0A0"},
    "bearish":  {"icon": "🔴", "label": "Медвежий",  "color": "#FF6B6B"},
    "neutral":  {"icon": "🟡", "label": "Нейтральный","color": "#F59E0B"},
    "buy":      {"icon": "🟢", "label": "Покупать",  "color": "#00F0A0"},
    "sell":     {"icon": "🔴", "label": "Продавать", "color": "#FF6B6B"},
    "hold":     {"icon": "🟡", "label": "Держать",   "color": "#F59E0B"},
}


def _signal_cfg(signal_raw):
    key = str(signal_raw).lower().strip()
    return SIGNAL_CONFIG.get(key, {"icon": "⚪", "label": signal_raw, "color": theme["subtext"]})


with st.spinner("Загрузка AI-сигналов..."):
    signals, api_ok = get_all_signals()

if not api_ok:
    st.warning("⚠️ Не удалось загрузить сигналы с API. Эндпоинт `/api/v1/signals` может быть в разработке.")

if signals:
    bulls = sum(1 for s in signals if str(s.get("signal", s.get("action", ""))).lower() in ("bullish", "buy"))
    bears = sum(1 for s in signals if str(s.get("signal", s.get("action", ""))).lower() in ("bearish", "sell"))
    neutral = len(signals) - bulls - bears

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Всего монет", len(signals))
    with col2:
        st.metric("🟢 Бычьих", bulls)
    with col3:
        st.metric("🔴 Медвежьих", bears)
    with col4:
        st.metric("🟡 Нейтральных", neutral)

    st.markdown("---")

    signal_filter = st.selectbox(
        "Фильтр по сигналу",
        ["Все", "Бычий / Покупать", "Медвежий / Продавать", "Нейтральный / Держать"],
    )

    filtered = signals
    if signal_filter == "Бычий / Покупать":
        filtered = [s for s in signals if str(s.get("signal", s.get("action", ""))).lower() in ("bullish", "buy")]
    elif signal_filter == "Медвежий / Продавать":
        filtered = [s for s in signals if str(s.get("signal", s.get("action", ""))).lower() in ("bearish", "sell")]
    elif signal_filter == "Нейтральный / Держать":
        filtered = [s for s in signals if str(s.get("signal", s.get("action", ""))).lower() in ("neutral", "hold")]

    st.subheader(f"Сигналы ({len(filtered)} монет)")

    tab_table, tab_cards = st.tabs(["📊 Таблица", "🃏 Карточки"])

    with tab_table:
        rows = []
        for s in filtered:
            sig_raw = s.get("signal", s.get("action", "neutral"))
            cfg = _signal_cfg(sig_raw)
            prob = s.get("probability", s.get("confidence", s.get("score", 0)))
            rows.append({
                "Монета": s.get("symbol", ""),
                "Сигнал": f"{cfg['icon']} {cfg['label']}",
                "Уверенность (%)": f"{float(prob)*100:.1f}%" if prob and float(prob) <= 1 else f"{float(prob):.1f}%" if prob else "N/A",
                "RSI": s.get("rsi", s.get("indicators", {}).get("rsi", "N/A")) if isinstance(s.get("indicators"), dict) else s.get("rsi", "N/A"),
                "MACD": s.get("macd", s.get("indicators", {}).get("macd", "N/A")) if isinstance(s.get("indicators"), dict) else s.get("macd", "N/A"),
                "Обновлено": s.get("updated_at", s.get("timestamp", "N/A")),
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab_cards:
        card_cols = st.columns(3)
        for i, s in enumerate(filtered):
            sig_raw = s.get("signal", s.get("action", "neutral"))
            cfg = _signal_cfg(sig_raw)
            symbol = s.get("symbol", "")
            prob = s.get("probability", s.get("confidence", s.get("score", 0)))
            prob_str = f"{float(prob)*100:.1f}%" if prob and float(prob) <= 1 else f"{float(prob):.1f}%" if prob else "—"
            rsi = s.get("rsi", "—")
            if isinstance(s.get("indicators"), dict):
                rsi = s["indicators"].get("rsi", rsi)
            with card_cols[i % 3]:
                st.markdown(
                    f"""
                    <div style="background:{theme['card_bg']};border:2px solid {cfg['color']};border-radius:12px;padding:14px;margin:6px 0">
                        <div style="font-size:1.3em;font-weight:bold;color:{cfg['color']}">{cfg['icon']} {symbol}</div>
                        <div style="color:{theme['text']};margin:4px 0">{cfg['label']}</div>
                        <div style="color:{theme['subtext']};font-size:0.85em">Уверенность: {prob_str}</div>
                        <div style="color:{theme['subtext']};font-size:0.85em">RSI: {rsi}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("---")
    st.subheader("📈 Детальный анализ монеты")

    all_symbols = [s.get("symbol", "") for s in signals if s.get("symbol")]
    selected_symbol = st.selectbox("Выберите монету", all_symbols)

    if selected_symbol:
        with st.spinner(f"Загрузка данных для {selected_symbol}..."):
            detail, det_ok = get_signal(selected_symbol)

        if det_ok and detail:
            sig_raw = detail.get("signal", detail.get("action", "neutral"))
            cfg = _signal_cfg(sig_raw)
            prob = detail.get("probability", detail.get("confidence", detail.get("score", 0)))
            prob_val = float(prob) * 100 if prob and float(prob) <= 1 else float(prob) if prob else 0
            indicators = detail.get("indicators", {}) if isinstance(detail.get("indicators"), dict) else {}

            col_sig, col_gauge = st.columns([2, 3])
            with col_sig:
                st.markdown(
                    f"""
                    <div style="background:{theme['card_bg']};border:2px solid {cfg['color']};border-radius:16px;padding:24px;text-align:center">
                        <div style="font-size:2em">{cfg['icon']}</div>
                        <div style="font-size:1.5em;font-weight:bold;color:{cfg['color']};margin:8px 0">{selected_symbol}</div>
                        <div style="font-size:1.2em;color:{theme['text']}">{cfg['label']}</div>
                        <div style="color:{theme['subtext']};margin-top:8px">Уверенность: <strong>{prob_val:.1f}%</strong></div>
                        <div style="color:{theme['subtext']};font-size:0.85em">Обновлено: {detail.get('updated_at', detail.get('timestamp', 'N/A'))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_gauge:
                if indicators:
                    ind_cols = st.columns(len(indicators))
                    for idx, (k, v) in enumerate(indicators.items()):
                        with ind_cols[idx]:
                            try:
                                st.metric(k.upper(), f"{float(v):.2f}")
                            except Exception:
                                st.metric(k.upper(), str(v))
                if detail.get("description") or detail.get("reason"):
                    st.info(detail.get("description", detail.get("reason", "")))
        else:
            from_list = next((s for s in signals if s.get("symbol") == selected_symbol), None)
            if from_list:
                sig_raw = from_list.get("signal", from_list.get("action", "neutral"))
                cfg = _signal_cfg(sig_raw)
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <strong style="color:{cfg['color']}">{cfg['icon']} {cfg['label']}</strong> для <strong>{selected_symbol}</strong>
                        — детальные данные недоступны (эндпоинт `/api/v1/signals/{"{symbol}"}` в разработке)
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
else:
    st.info("⚙️ Эндпоинт AI-сигналов (`/api/v1/signals`) в разработке на стороне API. Данные появятся автоматически после его запуска.")

    st.markdown("---")
    st.subheader("Ручная проверка сигнала для монеты")
    prices, _ = get_prices()
    symbols = [p["symbol"] for p in prices] if prices else []
    selected = st.selectbox("Монета", symbols) if symbols else st.text_input("Тикер монеты")
    if selected and st.button("Получить сигнал"):
        detail, ok = get_signal(selected)
        if ok and detail:
            st.json(detail)
        else:
            st.warning(f"Сигнал для {selected} недоступен. Эндпоинт в разработке.")
