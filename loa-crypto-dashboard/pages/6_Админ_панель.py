import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.api_client import get_all_users, get_logs, set_subscription, delete_user_data
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

if not users_ok:
    st.caption("⚠️ Не удалось загрузить список пользователей с API.")

tab1, tab2, tab3 = st.tabs(["👥 Пользователи", "🎫 Подписки", "📋 Логи"])

with tab1:
    st.subheader("Управление пользователями")

    if users:
        total = len(users)
        active = sum(1 for u in users if u.get("active", u.get("is_active", True)))
        admins = sum(1 for u in users if u.get("is_admin") or u.get("role") == "admin")
        experts = sum(1 for u in users if u.get("plan", u.get("subscription", "")) == "expert")

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
        search_query = st.text_input("🔍 Поиск пользователя", placeholder="Имя или VK ID...")

        filtered_users = users
        if search_query:
            filtered_users = [
                u for u in users
                if search_query.lower() in str(u.get("username", u.get("name", ""))).lower()
                or search_query in str(u.get("vk_id", u.get("user_id", "")))
            ]

        if filtered_users:
            display_rows = []
            for u in filtered_users:
                is_admin_u = u.get("is_admin") or u.get("role") == "admin"
                plan = u.get("plan", u.get("subscription", "free"))
                active_u = u.get("active", u.get("is_active", True))
                display_rows.append({
                    "VK ID": str(u.get("vk_id", u.get("user_id", ""))),
                    "Имя": u.get("username", u.get("name", "N/A")),
                    "Роль": "👑 Администратор" if is_admin_u else "👤 Пользователь",
                    "Подписка": {"expert": "⭐ Эксперт", "free": "🆓 Бесплатно", "admin": "🔑 Админ"}.get(plan, plan),
                    "Статус": "✅ Активен" if active_u else "🚫 Заблокирован",
                    "Регистрация": u.get("created_at", u.get("registered_at", "N/A")),
                })
            df = pd.DataFrame(display_rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Пользователи не найдены.")
    else:
        st.info("Список пользователей пуст или API недоступен.")

    st.markdown("---")
    st.subheader("Удаление данных пользователя")
    with st.form("delete_user_data_form"):
        del_target_id = st.text_input("VK ID пользователя")
        del_confirm = st.text_input("Введите 'УДАЛИТЬ' для подтверждения")
        del_submitted = st.form_submit_button("Удалить данные", type="primary")
        if del_submitted:
            if del_target_id and del_confirm == "УДАЛИТЬ":
                ok = delete_user_data(del_target_id)
                if ok:
                    st.success(f"✅ Данные пользователя {del_target_id} удалены.")
                else:
                    st.error("❌ Не удалось удалить данные. Проверьте API.")
            elif del_confirm != "УДАЛИТЬ":
                st.error("Введите 'УДАЛИТЬ' для подтверждения.")
            else:
                st.warning("Введите VK ID пользователя.")

with tab2:
    st.subheader("Выдача подписки пользователю")

    with st.form("subscription_form"):
        sub_user_id = st.text_input("VK ID пользователя")
        sub_type = st.selectbox(
            "Тип подписки",
            ["free", "expert"],
            format_func=lambda x: {"free": "🆓 Бесплатно", "expert": "⭐ Эксперт"}[x],
        )
        sub_comment = st.text_input("Комментарий (необязательно)")
        submitted_sub = st.form_submit_button("Выдать подписку")
        if submitted_sub:
            if sub_user_id.strip():
                ok = set_subscription(sub_user_id.strip(), sub_type)
                if ok:
                    st.success(f"✅ Подписка '{sub_type}' выдана пользователю {sub_user_id}")
                else:
                    st.error("❌ Не удалось выдать подписку. Проверьте API.")
            else:
                st.warning("Введите VK ID пользователя.")

    if users:
        st.markdown("---")
        st.subheader("Статистика подписок")
        sub_counts: dict = {}
        for u in users:
            plan = u.get("plan", u.get("subscription", "free"))
            sub_counts[plan] = sub_counts.get(plan, 0) + 1

        labels = {"free": "🆓 Бесплатно", "expert": "⭐ Эксперт", "admin": "🔑 Администратор"}
        cols = st.columns(max(len(sub_counts), 1))
        for i, (sub, count) in enumerate(sub_counts.items()):
            with cols[i]:
                st.metric(labels.get(sub, sub), count)

with tab3:
    st.subheader("Системные логи")

    if not logs_ok:
        st.warning("⚠️ Не удалось загрузить логи с API.")

    if logs:
        level_filter = st.selectbox("Уровень лога", ["Все", "INFO", "WARN", "WARNING", "ERROR"])

        filtered_logs = logs
        if level_filter != "Все":
            filtered_logs = [
                l for l in logs
                if l.get("level", "").upper() in (level_filter, level_filter.replace("WARN", "WARNING"))
            ]

        st.caption(f"Показано записей: {len(filtered_logs)}")
        for log in filtered_logs:
            level = str(log.get("level", "INFO")).upper()
            color = {"INFO": theme["positive"], "WARN": theme["accent2"], "WARNING": theme["accent2"], "ERROR": theme["negative"]}.get(level, theme["text"])
            ts = log.get("timestamp", log.get("created_at", log.get("time", "")))
            user_ref = log.get("user_id", log.get("vk_id", ""))
            action = log.get("action", log.get("event", log.get("message", "")))
            details = log.get("details", log.get("data", ""))
            st.markdown(
                f"""
                <div class="metric-card" style="margin:4px 0;padding:8px 16px">
                    <span style="color:{color};font-weight:bold">[{level}]</span>
                    <span style="color:{theme['subtext']}"> {ts} |</span>
                    <strong> {f"user:{user_ref} | " if user_ref else ""}{action}</strong>
                    {f'<span style="color:{theme["subtext"]}"> — {details}</span>' if details else ""}
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("Логи пусты.")
