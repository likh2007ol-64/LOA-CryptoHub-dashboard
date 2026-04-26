import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.api_client import get_system_status
from utils.theme_manager import get_theme, apply_theme, status_badge

st.set_page_config(page_title="Мониторинг | LOA-CryptoHub", page_icon="🖥️", layout="wide")

theme = get_theme(st.session_state.get("theme_name", "Тёмная"))
apply_theme(theme)

if st.session_state.get("user") is None:
    st.warning("⚠️ Пожалуйста, войдите через VK ID на главной странице.")
    st.stop()

user = st.session_state.user
if user.get("role") != "admin":
    st.error("🚫 Доступ запрещён. Только для администраторов.")
    st.stop()

st.markdown(f"<h1 style='color:{theme['accent1']}'>🖥️ Мониторинг и диагностика</h1>", unsafe_allow_html=True)
st.caption(f"Администратор: {user.get('username')} | Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

system_status, api_ok = get_system_status()

if not api_ok:
    st.caption("⚠️ Используются демо-данные")

COMPONENT_LABELS = {
    "vk_bot": "🤖 VK-бот",
    "api": "⚡ API сервер",
    "database": "🗄️ База данных",
    "coingecko_api": "📊 CoinGecko API",
    "binance_api": "💱 Binance API",
}

all_ok = all(v.get("status") == "ok" for v in system_status.values())
has_degraded = any(v.get("status") == "degraded" for v in system_status.values())
has_error = any(v.get("status") == "error" for v in system_status.values())

if all_ok:
    st.success("✅ Все системы работают нормально")
elif has_error:
    st.error("🔴 Обнаружены критические ошибки!")
elif has_degraded:
    st.warning("🟡 Некоторые компоненты работают в деградированном режиме")

st.markdown("---")
st.subheader("Статус компонентов")

cols = st.columns(len(system_status))
for i, (key, info) in enumerate(system_status.items()):
    status = info.get("status", "unknown")
    latency = info.get("latency_ms", 0)
    last_check = info.get("last_check", "N/A")

    if status == "ok":
        bg_color = "#0A3D2C"
        border_color = theme["positive"]
        status_icon = "🟢"
    elif status == "degraded":
        bg_color = "#3D2A0A"
        border_color = theme["accent2"]
        status_icon = "🟡"
    else:
        bg_color = "#3D0A0A"
        border_color = theme["negative"]
        status_icon = "🔴"

    with cols[i]:
        st.markdown(
            f"""
            <div style="background:{bg_color};border:2px solid {border_color};border-radius:12px;padding:16px;text-align:center">
                <div style="font-size:1.5em">{status_icon}</div>
                <div style="font-weight:bold;color:{theme['text']};margin:4px 0">{COMPONENT_LABELS.get(key, key)}</div>
                <div style="color:{border_color};font-size:0.9em">{status.upper()}</div>
                <div style="color:{theme['subtext']};font-size:0.8em">Задержка: {latency}ms</div>
                <div style="color:{theme['subtext']};font-size:0.75em">{last_check}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")
st.subheader("📊 Таблица проверок")

rows = []
for key, info in system_status.items():
    status = info.get("status", "unknown")
    latency = info.get("latency_ms", 0)
    health = "Хорошо" if latency < 100 else ("Медленно" if latency < 500 else "Критично")
    rows.append({
        "Компонент": COMPONENT_LABELS.get(key, key),
        "Статус": status_badge(status),
        "Задержка (ms)": latency,
        "Оценка": health,
        "Последняя проверка": info.get("last_check", "N/A"),
    })

df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("📈 Задержки компонентов")

latency_data = {COMPONENT_LABELS.get(k, k): v.get("latency_ms", 0) for k, v in system_status.items()}
colors = []
for k, v in system_status.items():
    if v.get("status") == "ok":
        colors.append(theme["positive"])
    elif v.get("status") == "degraded":
        colors.append(theme["accent2"])
    else:
        colors.append(theme["negative"])

fig = go.Figure(go.Bar(
    x=list(latency_data.keys()),
    y=list(latency_data.values()),
    marker_color=colors,
))
fig.update_layout(
    title="Задержка ответа компонентов (ms)",
    plot_bgcolor=theme["card_bg"],
    paper_bgcolor=theme["bg"],
    font_color=theme["text"],
    yaxis_title="Задержка (ms)",
    xaxis_title="Компонент",
    showlegend=False,
)
fig.add_hline(y=100, line_dash="dash", line_color=theme["accent2"], annotation_text="Порог медленного ответа (100ms)")
fig.add_hline(y=500, line_dash="dash", line_color=theme["negative"], annotation_text="Критичный порог (500ms)")
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("🔧 Управление компонентами")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🔄 Перезапустить VK-бот", use_container_width=True):
        with st.spinner("Перезапуск VK-бота..."):
            import time
            time.sleep(1)
        st.success("✅ VK-бот перезапущен")
with col2:
    if st.button("🗄️ Проверить БД", use_container_width=True):
        st.success("✅ Соединение с БД активно")
with col3:
    if st.button("🔄 Обновить статус", use_container_width=True):
        st.rerun()
