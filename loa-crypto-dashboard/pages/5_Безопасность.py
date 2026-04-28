import streamlit as st
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.api_client import delete_user_data
from utils.theme_manager import get_theme, apply_theme

st.set_page_config(page_title="Безопасность | LOA-CryptoHub", page_icon="🔒", layout="wide")

theme = get_theme(st.session_state.get("theme_name", "Тёмная"))
apply_theme(theme)

if st.session_state.get("user") is None:
    st.warning("⚠️ Пожалуйста, войдите через VK ID на главной странице.")
    st.stop()

user = st.session_state.user
user_id = user.get("user_id", "")

st.markdown(f"<h1 style='color:{theme['accent1']}'>🔒 Безопасность аккаунта</h1>", unsafe_allow_html=True)
st.caption(f"Пользователь: {user.get('username', user_id)} | VK ID: {user_id}")

st.subheader("🛡️ Статус сессии")

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

col1, col2 = st.columns(2)
with col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div style="font-size:1.1em;font-weight:bold;color:{theme['text']}">Информация о сессии</div>
            <br/>
            <div><strong>Статус:</strong> <span style="color:{theme['positive']}">✅ Активна</span></div>
            <div><strong>Пользователь:</strong> {user.get('username', 'N/A')}</div>
            <div><strong>VK ID:</strong> {user.get('vk_id', 'N/A')}</div>
            <div><strong>Роль:</strong> {user.get('role', 'user')}</div>
            <div><strong>Подписка:</strong> {user.get('subscription', 'free')}</div>
            <div><strong>Email:</strong> {user.get('email', 'N/A')}</div>
            <div style="color:{theme['subtext']};margin-top:8px">Время входа: {now}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div style="font-size:1.1em;font-weight:bold;color:{theme['text']}">Активность аккаунта</div>
            <br/>
            <div><strong>Последний вход:</strong> {now}</div>
            <div><strong>Устройство:</strong> Веб-браузер</div>
            <div><strong>Метод входа:</strong> VK ID</div>
            <div><strong>2FA:</strong> <span style="color:{theme['negative']}">Не настроено</span></div>
            <div style="color:{theme['subtext']};margin-top:8px">
                Рекомендуем настроить двухфакторную аутентификацию для защиты аккаунта.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")
st.subheader("🔐 Управление доступом")

col3, col4 = st.columns(2)
with col3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div style="font-size:1.1em;font-weight:bold;color:{theme['text']}">Разрешения</div>
            <br/>
            <div>{'✅' if user.get('subscription') in ['expert', 'admin'] else '❌'} Просмотр курсов в реальном времени</div>
            <div>{'✅' if user.get('subscription') in ['expert', 'admin'] else '❌'} Управление портфелем</div>
            <div>{'✅' if user.get('subscription') in ['expert', 'admin'] else '❌'} Ценовые уведомления</div>
            <div>{'✅' if user.get('subscription') in ['expert', 'admin'] else '❌'} Аналитические отчёты</div>
            <div>{'✅' if user.get('role') == 'admin' else '❌'} Администрирование системы</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div style="font-size:1.1em;font-weight:bold;color:{theme['text']}">API-доступ</div>
            <br/>
            <div style="color:{theme['subtext']}">API-ключ не сгенерирован</div>
            <br/>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Сгенерировать API-ключ", use_container_width=True):
        st.info("Функция генерации API-ключей доступна в полной версии платформы.")

st.markdown("---")
st.subheader("⚠️ Опасная зона")

st.markdown(
    f"""
    <div class="metric-card" style="border-color:{theme['negative']}">
        <div style="font-size:1.1em;font-weight:bold;color:{theme['negative']}">Удаление данных</div>
        <p style="color:{theme['subtext']}">
            Это действие безвозвратно удалит все ваши данные: портфель, историю транзакций, 
            уведомления, отчёты и настройки. Действие необратимо.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("🗑️ Удалить мои данные (необратимо)"):
    st.error("⚠️ Внимание! Это действие нельзя отменить!")
    confirm = st.text_input("Для подтверждения введите 'УДАЛИТЬ':")
    if st.button("Удалить все мои данные", type="primary"):
        if confirm == "УДАЛИТЬ":
            ok = delete_user_data(user_id)
            st.success("Ваши данные удалены. Сессия завершена.")
            st.session_state.user = None
            st.rerun()
        else:
            st.error("Введите 'УДАЛИТЬ' для подтверждения.")

if st.button("🚪 Завершить сессию", use_container_width=True):
    st.session_state.user = None
    st.success("Сессия завершена.")
    st.rerun()
