import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.api_client import get_all_users, get_logs, set_subscription, delete_user_data, get_metrics
from utils.theme_manager import get_theme, apply_theme

st.set_page_config(page_title="Админ-панель | LOA-CryptoHub", page_icon="👑", layout="wide")

theme = get_theme(st.session_state.get("theme_name", "Тёмная"))
apply_theme(theme)

if st.session_state.get("user") is None:
    st.warning("⚠️ Пожалуйста, войдите через VK ID на главной странице.")
    st.stop()

user = st.session_state.user
if user.get("role") != "admin" and not user.get("is_admin"):
    st.error("🚫 Доступ запрещён. Только для администраторов.")
    st.stop()

st.markdown(f"<h1 style='color:{theme['accent1']}'>👑 Административная панель</h1>", unsafe_allow_html=True)
st.caption(f"Администратор: {user.get('username', user.get('user_id'))} | VK ID: {user.get('user_id')}")

users, users_ok = get_all_users()
logs, logs_ok = get_logs()
metrics_data, metrics_ok = get_metrics()

if not users_ok:
    st.caption("⚠️ Список пользователей недоступен.")

tab1, tab2, tab3, tab4 = st.tabs(["👥 Пользователи", "🎫 Подписки", "📋 Логи", "📈 Метрики"])

# -----------------------------------------------------------------------
with tab1:
    st.subheader("Управление пользователями")

    if users:
        total = len(users)
        active = sum(1 for u in users if u.get("active", u.get("is_active", True)))
        admins = sum(1 for u in users if u.get("is_admin") or u.get("role") == "admin")
        experts = sum(1 for u in users if u.get("plan", u.get("subscription", "")) == "expert")

        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Всего", total)
        with col2: st.metric("Активных", active)
        with col3: st.metric("Администраторов", admins)
        with col4: st.metric("Экспертов", experts)

        st.markdown("---")
        search = st.text_input("🔍 Поиск", placeholder="Имя или VK ID...")
        filtered = users if not search else [
            u for u in users
            if search.lower() in str(u.get("username", u.get("name", ""))).lower()
            or search in str(u.get("vk_id", u.get("user_id", "")))
        ]

        if filtered:
            display = []
            for u in filtered:
                is_admin_u = u.get("is_admin") or u.get("role") == "admin"
                plan = u.get("plan", u.get("subscription", "free"))
                display.append({
                    "VK ID":      str(u.get("vk_id", u.get("user_id", ""))),
                    "Имя":        u.get("username", u.get("name", "N/A")),
                    "Роль":       "👑 Адм." if is_admin_u else "👤 Польз.",
                    "Подписка":   {"expert": "⭐ Эксперт", "free": "🆓 Free", "admin": "🔑 Админ"}.get(plan, plan),
                    "Статус":     "✅ Активен" if u.get("active", u.get("is_active", True)) else "🚫 Заблок.",
                    "Создан":     u.get("created_at", u.get("registered_at", "N/A")),
                })
            st.dataframe(pd.DataFrame(display), use_container_width=True, hide_index=True)
        else:
            st.info("Пользователи не найдены.")
    else:
        st.info("Список пользователей пуст или API недоступен.")

    st.markdown("---")
    st.subheader("Удаление данных пользователя")
    with st.form("delete_user_data_form"):
        del_id = st.text_input("VK ID пользователя")
        del_confirm = st.text_input("Введите 'УДАЛИТЬ' для подтверждения")
        if st.form_submit_button("Удалить данные", type="primary"):
            if del_id and del_confirm == "УДАЛИТЬ":
                ok = delete_user_data(del_id)
                st.success(f"✅ Данные пользователя {del_id} удалены.") if ok else st.error("❌ Не удалось удалить.")
            elif del_confirm != "УДАЛИТЬ":
                st.error("Введите 'УДАЛИТЬ' для подтверждения.")
            else:
                st.warning("Введите VK ID.")

# -----------------------------------------------------------------------
with tab2:
    st.subheader("Выдача подписки")
    with st.form("subscription_form"):
        sub_id = st.text_input("VK ID пользователя")
        sub_type = st.selectbox("Тип подписки", ["free", "expert"],
                                format_func=lambda x: {"free": "🆓 Бесплатно", "expert": "⭐ Эксперт"}[x])
        sub_comment = st.text_input("Комментарий (необязательно)")
        if st.form_submit_button("Выдать подписку"):
            if sub_id.strip():
                ok = set_subscription(sub_id.strip(), sub_type)
                st.success(f"✅ Подписка '{sub_type}' выдана пользователю {sub_id}") if ok else st.error("❌ Не удалось выдать подписку.")
            else:
                st.warning("Введите VK ID.")

    if users:
        st.markdown("---")
        st.subheader("Статистика подписок")
        sub_counts: dict = {}
        for u in users:
            p = u.get("plan", u.get("subscription", "free"))
            sub_counts[p] = sub_counts.get(p, 0) + 1
        labels = {"free": "🆓 Бесплатно", "expert": "⭐ Эксперт", "admin": "🔑 Адм."}
        cols = st.columns(max(len(sub_counts), 1))
        for i, (sub, cnt) in enumerate(sub_counts.items()):
            with cols[i]: st.metric(labels.get(sub, sub), cnt)

        if len(sub_counts) > 1:
            fig_pie = px.pie(
                values=list(sub_counts.values()),
                names=[labels.get(k, k) for k in sub_counts.keys()],
                title="Распределение подписок",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_pie.update_layout(paper_bgcolor=theme["bg"], font_color=theme["text"])
            st.plotly_chart(fig_pie, use_container_width=True)

# -----------------------------------------------------------------------
with tab3:
    st.subheader("Системные логи")
    if not logs_ok:
        st.warning("⚠️ Логи недоступны с API.")

    if logs:
        level_filter = st.selectbox("Уровень", ["Все", "INFO", "WARN", "WARNING", "ERROR"])
        filtered_logs = logs if level_filter == "Все" else [
            l for l in logs if str(l.get("level", "")).upper() in (level_filter, level_filter.replace("WARN", "WARNING"))
        ]
        st.caption(f"Показано: {len(filtered_logs)} записей")
        for log in filtered_logs:
            level = str(log.get("level", "INFO")).upper()
            color = {"INFO": theme["positive"], "WARN": theme["accent2"], "WARNING": theme["accent2"], "ERROR": theme["negative"]}.get(level, theme["text"])
            ts = log.get("timestamp", log.get("created_at", log.get("time", "")))
            user_ref = log.get("user_id", log.get("vk_id", ""))
            action = log.get("action", log.get("event", log.get("message", "")))
            details = log.get("details", log.get("data", ""))
            st.markdown(
                f"""<div class="metric-card" style="margin:3px 0;padding:7px 14px">
                    <span style="color:{color};font-weight:bold">[{level}]</span>
                    <span style="color:{theme['subtext']}"> {ts}</span>
                    {f'<span> | user:{user_ref}</span>' if user_ref else ""}
                    <strong> {action}</strong>
                    {f'<span style="color:{theme["subtext"]}"> — {details}</span>' if details else ""}
                </div>""",
                unsafe_allow_html=True,
            )
    else:
        st.info("Логи пусты.")

# -----------------------------------------------------------------------
with tab4:
    st.subheader("📈 Метрики системы")
    st.caption("Эндпоинт: `GET /api/v1/admin/metrics`")

    if not metrics_ok:
        st.warning("⚠️ Эндпоинт `/api/v1/admin/metrics` недоступен или в разработке.")

    if metrics_data and isinstance(metrics_data, dict):
        scalar = {k: v for k, v in metrics_data.items() if isinstance(v, (int, float, str)) and not isinstance(v, bool)}
        series = {k: v for k, v in metrics_data.items() if isinstance(v, list)}

        if scalar:
            mcols = st.columns(min(len(scalar), 4))
            for i, (k, v) in enumerate(scalar.items()):
                with mcols[i % 4]:
                    try:
                        st.metric(k.replace("_", " ").title(), f"{float(v):,.0f}" if isinstance(v, (int, float)) else v)
                    except Exception:
                        st.metric(k.replace("_", " ").title(), str(v))

        for k, s in series.items():
            if s and isinstance(s[0], dict):
                df_s = pd.DataFrame(s)
                time_col = next((c for c in ("timestamp", "time", "date", "ts") if c in df_s.columns), None)
                val_col = next((c for c in df_s.columns if c != time_col), None)
                if time_col and val_col:
                    fig = px.line(df_s, x=time_col, y=val_col, title=k.replace("_", " ").title(), color_discrete_sequence=[theme["accent1"]])
                    fig.update_layout(plot_bgcolor=theme["card_bg"], paper_bgcolor=theme["bg"], font_color=theme["text"])
                    st.plotly_chart(fig, use_container_width=True)
    elif metrics_data:
        st.json(metrics_data)
    else:
        st.info("Данные метрик появятся после запуска эндпоинта `/api/v1/admin/metrics`.")

        if users:
            st.markdown("---")
            st.subheader("📊 Аналитика пользователей (из имеющихся данных)")
            sub_counts: dict = {}
            for u in users:
                p = u.get("plan", u.get("subscription", "free"))
                sub_counts[p] = sub_counts.get(p, 0) + 1
            labels_map = {"free": "Бесплатно", "expert": "Эксперт", "admin": "Администратор"}
            fig = go.Figure(go.Bar(
                x=[labels_map.get(k, k) for k in sub_counts.keys()],
                y=list(sub_counts.values()),
                marker_color=[theme["accent1"], theme["accent2"], theme["positive"]][:len(sub_counts)],
            ))
            fig.update_layout(title="Пользователи по типу подписки", plot_bgcolor=theme["card_bg"], paper_bgcolor=theme["bg"], font_color=theme["text"])
            st.plotly_chart(fig, use_container_width=True)
