import streamlit as st

THEMES = {
    "Тёмная": {
        "bg": "#0A2540",
        "card_bg": "#1E1E2F",
        "accent1": "#00F0A0",
        "accent2": "#F5B041",
        "text": "#FFFFFF",
        "subtext": "#A0AEC0",
        "positive": "#00F0A0",
        "negative": "#FF6B6B",
        "border": "#2D3748",
    },
    "Светлая": {
        "bg": "#F7FAFC",
        "card_bg": "#FFFFFF",
        "accent1": "#3182CE",
        "accent2": "#E53E3E",
        "text": "#1A202C",
        "subtext": "#718096",
        "positive": "#38A169",
        "negative": "#E53E3E",
        "border": "#E2E8F0",
    },
    "Неон": {
        "bg": "#0D0D1A",
        "card_bg": "#1A1A2E",
        "accent1": "#FF00FF",
        "accent2": "#00FFFF",
        "text": "#FFFFFF",
        "subtext": "#CC99FF",
        "positive": "#00FF88",
        "negative": "#FF3366",
        "border": "#330066",
    },
    "Синяя": {
        "bg": "#1A237E",
        "card_bg": "#283593",
        "accent1": "#82B1FF",
        "accent2": "#FFD740",
        "text": "#FFFFFF",
        "subtext": "#BBDEFB",
        "positive": "#69F0AE",
        "negative": "#FF6E40",
        "border": "#3949AB",
    },
}


def get_theme(name: str) -> dict:
    return THEMES.get(name, THEMES["Тёмная"])


def apply_theme(theme: dict):
    css = f"""
    <style>
    .stApp {{
        background-color: {theme['bg']};
        color: {theme['text']};
    }}
    .metric-card {{
        background-color: {theme['card_bg']};
        border: 1px solid {theme['border']};
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
    }}
    .price-positive {{
        color: {theme['positive']};
        font-weight: bold;
    }}
    .price-negative {{
        color: {theme['negative']};
        font-weight: bold;
    }}
    .accent-text {{
        color: {theme['accent1']};
        font-weight: bold;
    }}
    .subtext {{
        color: {theme['subtext']};
        font-size: 0.85em;
    }}
    .status-ok {{
        color: {theme['positive']};
        font-weight: bold;
    }}
    .status-degraded {{
        color: {theme['accent2']};
        font-weight: bold;
    }}
    .status-error {{
        color: {theme['negative']};
        font-weight: bold;
    }}
    section[data-testid="stSidebar"] {{
        background-color: {theme['card_bg']};
        border-right: 1px solid {theme['border']};
    }}
    .stSelectbox, .stTextInput, .stNumberInput {{
        background-color: {theme['card_bg']};
    }}
    div[data-testid="stMetric"] {{
        background-color: {theme['card_bg']};
        border: 1px solid {theme['border']};
        border-radius: 10px;
        padding: 10px 16px;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def status_badge(status: str) -> str:
    if status == "ok":
        return "🟢 OK"
    elif status == "degraded":
        return "🟡 Деградация"
    else:
        return "🔴 Ошибка"
