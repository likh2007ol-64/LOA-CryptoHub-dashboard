import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.api_client import get_system_status, get_health_all, get_metrics, get_system_info
from utils.theme_manager import get_theme, apply_theme, status_badge

st.set_page_config(page_title="Мониторинг | LOA-CryptoHub", page_icon="🖥️", layout="wide")

theme = get_theme(st.session_state.get("theme_name", "Тёмная"))
apply_theme(theme)

if st.session_state.get("user") is None:
    st.warning("⚠️ Пожалуйста, войдите через VK ID на главной странице.")
    st.stop()

user = st.session_state.user
if user.get("role") != "admin" and not user.get("is_admin"):
    st.error("🚫 Доступ запрещён. Только для администраторов.")
    st.stop()

st.markdown(f"<h1 style='color:{theme['accent1']}'>🖥️ Мониторинг и диагностика</h1>", unsafe_allow_html=True)
st.caption(f"Администратор: {user.get('username', user.get('user_id'))} | Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

COMPONENT_LABELS = {
    "api":          "⚡ API сервер",
    "vk_bot":       "🤖 VK-бот",
    "database":     "🗄️ База данных",
    "coingecko_api":"📊 CoinGecko API",
    "binance_api":  "💱 Binance API",
}

tab_status, tab_health, tab_metrics, tab_sysinfo = st.tabs([
    "🟢 Статус компонентов",
    "🔍 Детальный Health-check",
    "📈 Метрики",
    "ℹ️ Система",
])

# -----------------------------------------------------------------------
with tab_status:
    with st.spinner("Проверка компонентов..."):
        system_status, api_ok = get_system_status()

    if not api_ok:
        st.error("🔴 API сервер недоступен!")
    else:
        st.success("✅ API сервер отвечает")

    known_statuses = {v.get("status") for v in system_status.values()}
    if "error" in known_statuses:
        st.error("🔴 Обнаружены критические ошибки в компонентах!")
    elif "degraded" in known_statuses:
        st.warning("🟡 Некоторые компоненты работают в деградированном режиме")
    elif any(s == "ok" for s in known_statuses):
        if "error" not in known_statuses and "degraded" not in known_statuses:
            st.success("✅ Все проверенные системы работают нормально")

    if system_status:
        cols = st.columns(len(system_status))
        for i, (key, info) in enumerate(system_status.items()):
            status = info.get("status", "unknown")
            latency = info.get("latency_ms", 0)
            if status == "ok":
                bg, border, icon = "#0A3D2C", theme["positive"], "🟢"
            elif status == "degraded":
                bg, border, icon = "#3D2A0A", theme["accent2"], "🟡"
            elif status == "error":
                bg, border, icon = "#3D0A0A", theme["negative"], "🔴"
            else:
                bg, border, icon = "#1A1A2E", theme["border"], "⚪"
            with cols[i]:
                st.markdown(
                    f"""<div style="background:{bg};border:2px solid {border};border-radius:12px;padding:16px;text-align:center">
                        <div style="font-size:1.5em">{icon}</div>
                        <div style="font-weight:bold;color:{theme['text']};margin:4px 0">{COMPONENT_LABELS.get(key, key)}</div>
                        <div style="color:{border};font-size:0.9em">{status.upper()}</div>
                        <div style="color:{theme['subtext']};font-size:0.8em">{f"Задержка: {latency}ms" if latency else ""}</div>
                        <div style="color:{theme['subtext']};font-size:0.75em">{info.get('last_check','')}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

        st.markdown("---")
        rows = []
        for key, info in system_status.items():
            latency = info.get("latency_ms", 0)
            health = "Хорошо" if 0 < latency < 100 else "Медленно" if latency < 500 else ("Критично" if latency >= 500 else "N/A")
            rows.append({
                "Компонент": COMPONENT_LABELS.get(key, key),
                "Статус": status_badge(info.get("status", "unknown")),
                "Задержка (ms)": latency or "—",
                "Оценка": health,
                "Проверено": info.get("last_check", "N/A"),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        latency_items = {k: v for k, v in system_status.items() if v.get("latency_ms", 0) > 0}
        if latency_items:
            lat_data = {COMPONENT_LABELS.get(k, k): v["latency_ms"] for k, v in latency_items.items()}
            colors = [theme["positive"] if latency_items[k]["status"] == "ok" else theme["accent2"] if latency_items[k]["status"] == "degraded" else theme["negative"] for k in latency_items]
            fig = go.Figure(go.Bar(x=list(lat_data.keys()), y=list(lat_data.values()), marker_color=colors))
            fig.update_layout(title="Задержка компонентов (ms)", plot_bgcolor=theme["card_bg"], paper_bgcolor=theme["bg"], font_color=theme["text"], showlegend=False)
            fig.add_hline(y=100, line_dash="dash", line_color=theme["accent2"], annotation_text="100ms")
            fig.add_hline(y=500, line_dash="dash", line_color=theme["negative"], annotation_text="500ms")
            st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Обновить статус", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col2:
        if st.button("🗄️ Проверить /health", use_container_width=True):
            from utils.api_client import _api_get
            data, ok = _api_get("/health")
            st.success(f"✅ {data}") if ok else st.error("❌ API не отвечает")
    with col3:
        if st.button("📊 Проверить /prices", use_container_width=True):
            from utils.api_client import _api_get
            data, ok = _api_get("/api/v1/prices/")
            count = len(data.get("data", data)) if ok and isinstance(data, dict) else (len(data) if ok and isinstance(data, list) else 0)
            st.success(f"✅ Цены: {count} монет") if ok else st.error("❌ Эндпоинт /prices/ не отвечает")

# -----------------------------------------------------------------------
with tab_health:
    st.subheader("🔍 Детальный health-check всех компонентов")
    st.caption("Эндпоинт: `GET /api/v1/admin/health/all`")

    with st.spinner("Загрузка детального статуса..."):
        health_all, h_ok = get_health_all()

    if not h_ok:
        st.warning("⚠️ Эндпоинт `/api/v1/admin/health/all` недоступен или в разработке.")
    elif health_all:
        if isinstance(health_all, dict):
            for component, details in health_all.items():
                with st.expander(f"{COMPONENT_LABELS.get(component, component)}", expanded=True):
                    if isinstance(details, dict):
                        status = details.get("status", "unknown")
                        color = theme["positive"] if status == "ok" else theme["negative"] if status == "error" else theme["accent2"]
                        st.markdown(f"**Статус:** <span style='color:{color}'>{status.upper()}</span>", unsafe_allow_html=True)
                        for k, v in details.items():
                            if k != "status":
                                st.markdown(f"**{k}:** {v}")
                    else:
                        st.write(details)
        elif isinstance(health_all, list):
            for item in health_all:
                st.json(item)
    else:
        st.info("Данных health/all не получено.")

# -----------------------------------------------------------------------
with tab_metrics:
    st.subheader("📈 Системные метрики")
    st.caption("Эндпоинт: `GET /api/v1/admin/metrics`")

    with st.spinner("Загрузка метрик..."):
        metrics_data, m_ok = get_metrics()

    if not m_ok:
        st.warning("⚠️ Эндпоинт `/api/v1/admin/metrics` недоступен или в разработке.")
    elif metrics_data:
        if isinstance(metrics_data, dict):
            scalar_metrics = {k: v for k, v in metrics_data.items() if isinstance(v, (int, float, str))}
            time_series = {k: v for k, v in metrics_data.items() if isinstance(v, list)}

            if scalar_metrics:
                mcols = st.columns(min(len(scalar_metrics), 4))
                for i, (k, v) in enumerate(scalar_metrics.items()):
                    with mcols[i % 4]:
                        try:
                            st.metric(k.replace("_", " ").title(), f"{float(v):,.2f}" if isinstance(v, float) else v)
                        except Exception:
                            st.metric(k.replace("_", " ").title(), str(v))

            for k, series in time_series.items():
                if series and isinstance(series[0], dict):
                    df_ts = pd.DataFrame(series)
                    time_col = next((c for c in ("timestamp", "time", "date", "ts") if c in df_ts.columns), None)
                    val_col = next((c for c in df_ts.columns if c not in (time_col,)), None)
                    if time_col and val_col:
                        fig = px.line(df_ts, x=time_col, y=val_col, title=k.replace("_", " ").title(),
                                      color_discrete_sequence=[theme["accent1"]])
                        fig.update_layout(plot_bgcolor=theme["card_bg"], paper_bgcolor=theme["bg"], font_color=theme["text"])
                        st.plotly_chart(fig, use_container_width=True)
        else:
            st.json(metrics_data)
    else:
        st.info("Метрики будут доступны после запуска эндпоинта `/api/v1/admin/metrics`.")

# -----------------------------------------------------------------------
with tab_sysinfo:
    st.subheader("ℹ️ Информация о системе")
    st.caption("Эндпоинт: `GET /api/v1/admin/system-info`")

    with st.spinner("Загрузка информации о системе..."):
        sys_info, si_ok = get_system_info()

    if not si_ok:
        st.warning("⚠️ Эндпоинт `/api/v1/admin/system-info` недоступен или в разработке.")
    elif sys_info:
        if isinstance(sys_info, dict):
            for section, content in sys_info.items():
                st.markdown(f"### {section.replace('_', ' ').title()}")
                if isinstance(content, dict):
                    for k, v in content.items():
                        st.markdown(f"- **{k}:** `{v}`")
                elif isinstance(content, list):
                    for item in content:
                        st.markdown(f"- {item}")
                else:
                    st.markdown(f"`{content}`")
        else:
            st.json(sys_info)
    else:
        st.info("Информация о системе будет доступна после запуска эндпоинта `/api/v1/admin/system-info`.")
