import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.api_client import get_all_users, get_logs
from utils.theme_manager import get_theme, apply_theme

st.set_page_config(page_title="Админ-панель | LOA-CryptoHub", page_icon="👑", layout="wide")

theme = get_theme(st.session_state.get("theme_name", "Тёмная"))
apply_theme(theme)

if st.session_state.get("user") is None:
    st.warning("⚠️ Пожалуйста, войдите через VK ID на главной странице.")
    st.stop()

user = st.session_state.user
if user.get("role") != "admin":
    st.error("🚫 Доступ запрещён. Только для администраторов.")
    st.stop()

st.markdown(f"<h1 style='color:{theme['accent1']}'>👑 Административная панель</h1>", unsafe_allow_html=True)
st.caption(f"Администратор: {user.get('username')} | ID: {user.get('user_id')}")

users, api_ok = get_all_users()
logs, _ = get_logs()

if not api_ok:
    st.caption("⚠️ Используются демо-данные")

tab1, tab2, tab3 = st.tabs(["👥 Пользователи", "🎫 Подписки", "📋 Логи"])

with tab1:
    st.subheader("Управление пользователями")

    total = len(users)
    active = sum(1 for u in users if u.get("active"))
    admins = sum(1 for u in users if u.get("role") == "admin")
    experts = sum(1 for u in users if u.get("subscription") == "expert")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Всего пользователей", total)
    with col2:
        st.metric("Активных", active)
    with col3:
        st.metric("Администраторов", admins)
    with col4:
        st.metric("Экспертов", experts)

    st.markdown("---")

    search_query = st.text_input("🔍 Поиск пользователя", placeholder="Имя или ID...")

    filtered_users = users
    if search_query:
        filtered_users = [
            u for u in users
            if search_query.lower() in u.get("username", "").lower()
            or search_query in str(u.get("user_id", ""))
        ]

    if filtered_users:
        df = pd.DataFrame(filtered_users)
        df["active"] = df["active"].apply(lambda x: "✅ Активен" if x else "🚫 Заблокирован")
        df["role"] = df["role"].apply(lambda x: "👑 Администратор" if x == "admin" else "👤 Пользователь")
        df["subscription"] = df["subscription"].apply(
            lambda x: {"admin": "🔑 Админ", "expert": "⭐ Эксперт", "free": "🆓 Бесплатно"}.get(x, x)
        )
        df = df[["user_id", "username", "role", "subscription", "active", "created_at"]]
        df.columns = ["ID", "Имя", "Роль", "Подписка", "Статус", "Регистрация"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Пользователи не найдены.")

    st.markdown("---")
    st.subheader("Действия с пользователем")
    with st.form("user_action_form"):
        target_id = st.text_input("ID пользователя")
        action = st.selectbox("Действие", ["Заблокировать", "Разблокировать", "Сбросить данные", "Назначить администратором"])
        reason = st.text_area("Причина (необязательно)")
        submitted = st.form_submit_button("Применить")
        if submitted:
            if target_id:
                st.success(f"✅ Действие '{action}' применено к пользователю {target_id}")
            else:
                st.warning("Введите ID пользователя")

with tab2:
    st.subheader("Управление подписками")

    st.markdown("Назначить подписку пользователю:")
    with st.form("subscription_form"):
        sub_user_id = st.text_input("ID пользователя")
        sub_type = st.selectbox("Тип подписки", ["free", "expert", "admin"],
                                format_func=lambda x: {"free": "🆓 Бесплатно", "expert": "⭐ Эксперт", "admin": "🔑 Администратор"}[x])
        sub_duration = st.selectbox("Срок", ["30 дней", "90 дней", "180 дней", "365 дней", "Бессрочно"])
        sub_reason = st.text_input("Комментарий")
        submitted_sub = st.form_submit_button("Выдать подписку")
        if submitted_sub:
            if sub_user_id:
                st.success(f"✅ Подписка '{sub_type}' ({sub_duration}) выдана пользователю {sub_user_id}")
            else:
                st.warning("Введите ID пользователя")

    st.markdown("---")
    st.subheader("Статистика подписок")
    if users:
        sub_counts = {}
        for u in users:
            sub = u.get("subscription", "free")
            sub_counts[sub] = sub_counts.get(sub, 0) + 1

        cols = st.columns(len(sub_counts))
        labels = {"free": "🆓 Бесплатно", "expert": "⭐ Эксперт", "admin": "🔑 Администратор"}
        for i, (sub, count) in enumerate(sub_counts.items()):
            with cols[i]:
                st.metric(labels.get(sub, sub), count)

with tab3:
    st.subheader("Системные логи")

    if logs:
        level_filter = st.selectbox("Уровень", ["Все", "INFO", "WARN", "ERROR"])

        filtered_logs = logs
        if level_filter != "Все":
            filtered_logs = [l for l in logs if l.get("level") == level_filter]

        for log in filtered_logs:
            level = log.get("level", "INFO")
            color = {"INFO": theme["positive"], "WARN": theme["accent2"], "ERROR": theme["negative"]}.get(level, theme["text"])
            st.markdown(
                f"""
                <div class="metric-card" style="margin:4px 0;padding:8px 16px">
                    <span style="color:{color};font-weight:bold">[{level}]</span>
                    <span style="color:{theme['subtext']}">{log.get('timestamp', '')} |</span>
                    <strong> user_id:{log.get('user_id', '')} | {log.get('action', '')}</strong>
                    <span style="color:{theme['subtext']}"> — {log.get('details', '')}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("Логи пусты.")
