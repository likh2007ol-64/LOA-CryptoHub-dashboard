import os
import requests
import pandas as pd
from datetime import datetime, timedelta
import random

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8080")
REQUEST_TIMEOUT = 5

MOCK_PRICES = [
    {"symbol": "BTC", "name": "Bitcoin", "price": 67432.50, "change_24h": 2.34, "market_cap": 1320000000000, "volume_24h": 28500000000},
    {"symbol": "ETH", "name": "Ethereum", "price": 3521.80, "change_24h": -1.12, "market_cap": 423000000000, "volume_24h": 14200000000},
    {"symbol": "BNB", "name": "BNB", "price": 598.40, "change_24h": 0.87, "market_cap": 89000000000, "volume_24h": 2100000000},
    {"symbol": "SOL", "name": "Solana", "price": 178.60, "change_24h": 5.21, "market_cap": 82000000000, "volume_24h": 4500000000},
    {"symbol": "XRP", "name": "XRP", "price": 0.5842, "change_24h": -0.45, "market_cap": 32000000000, "volume_24h": 1800000000},
    {"symbol": "DOGE", "name": "Dogecoin", "price": 0.1634, "change_24h": 3.76, "market_cap": 23500000000, "volume_24h": 1200000000},
    {"symbol": "ADA", "name": "Cardano", "price": 0.4521, "change_24h": -2.18, "market_cap": 16000000000, "volume_24h": 620000000},
    {"symbol": "AVAX", "name": "Avalanche", "price": 38.92, "change_24h": 1.55, "market_cap": 16000000000, "volume_24h": 780000000},
    {"symbol": "TRX", "name": "TRON", "price": 0.1287, "change_24h": 0.23, "market_cap": 11200000000, "volume_24h": 420000000},
    {"symbol": "DOT", "name": "Polkadot", "price": 7.43, "change_24h": -3.01, "market_cap": 10500000000, "volume_24h": 310000000},
]

MOCK_USERS = {
    "1": {"user_id": "1", "username": "user_demo", "role": "user", "email": "user@example.com", "subscription": "expert", "vk_id": "1"},
    "42": {"user_id": "42", "username": "admin_loa", "role": "admin", "email": "admin@loa.io", "subscription": "admin", "vk_id": "42"},
    "100": {"user_id": "100", "username": "expert_trader", "role": "user", "email": "expert@example.com", "subscription": "expert", "vk_id": "100"},
}

MOCK_PORTFOLIO = [
    {"symbol": "BTC", "amount": 0.15, "avg_buy_price": 58000.00, "buy_date": "2024-01-10"},
    {"symbol": "ETH", "amount": 2.5, "avg_buy_price": 2800.00, "buy_date": "2024-02-15"},
    {"symbol": "SOL", "amount": 20.0, "avg_buy_price": 120.00, "buy_date": "2024-03-01"},
]

MOCK_ALERTS = [
    {"id": "a1", "symbol": "BTC", "condition": "above", "target_price": 70000, "active": True, "created_at": "2024-04-01"},
    {"id": "a2", "symbol": "ETH", "condition": "below", "target_price": 3000, "active": True, "created_at": "2024-04-05"},
]

MOCK_TRANSACTIONS = [
    {"id": "t1", "type": "buy", "symbol": "BTC", "amount": 0.1, "price": 55000, "date": "2024-01-10", "total": 5500},
    {"id": "t2", "type": "buy", "symbol": "ETH", "amount": 1.5, "price": 2700, "date": "2024-02-15", "total": 4050},
    {"id": "t3", "type": "buy", "symbol": "SOL", "amount": 20, "price": 120, "date": "2024-03-01", "total": 2400},
    {"id": "t4", "type": "sell", "symbol": "BTC", "amount": 0.05, "price": 62000, "date": "2024-03-20", "total": 3100},
    {"id": "t5", "type": "buy", "symbol": "BTC", "amount": 0.1, "price": 61000, "date": "2024-04-01", "total": 6100},
    {"id": "t6", "type": "buy", "symbol": "ETH", "amount": 1.0, "price": 3100, "date": "2024-04-10", "total": 3100},
]

MOCK_SYSTEM_STATUS = {
    "vk_bot": {"status": "ok", "latency_ms": 45, "last_check": "2024-04-26 12:00:00"},
    "api": {"status": "ok", "latency_ms": 12, "last_check": "2024-04-26 12:00:00"},
    "database": {"status": "ok", "latency_ms": 8, "last_check": "2024-04-26 12:00:00"},
    "coingecko_api": {"status": "ok", "latency_ms": 210, "last_check": "2024-04-26 12:00:00"},
    "binance_api": {"status": "degraded", "latency_ms": 850, "last_check": "2024-04-26 12:00:00"},
}

MOCK_USERS_LIST = [
    {"user_id": "1", "username": "user_demo", "role": "user", "subscription": "expert", "active": True, "created_at": "2024-01-01"},
    {"user_id": "42", "username": "admin_loa", "role": "admin", "subscription": "admin", "active": True, "created_at": "2023-06-15"},
    {"user_id": "100", "username": "expert_trader", "role": "user", "subscription": "expert", "active": True, "created_at": "2024-02-20"},
    {"user_id": "200", "username": "free_user", "role": "user", "subscription": "free", "active": True, "created_at": "2024-03-10"},
    {"user_id": "300", "username": "banned_user", "role": "user", "subscription": "free", "active": False, "created_at": "2024-04-01"},
]

MOCK_LOGS = [
    {"timestamp": "2024-04-26 12:00:05", "level": "INFO", "user_id": "1", "action": "login", "details": "User logged in via VK"},
    {"timestamp": "2024-04-26 11:55:30", "level": "INFO", "user_id": "100", "action": "portfolio_view", "details": "Viewed portfolio"},
    {"timestamp": "2024-04-26 11:50:12", "level": "WARN", "user_id": "200", "action": "api_rate_limit", "details": "Rate limit reached"},
    {"timestamp": "2024-04-26 11:45:00", "level": "ERROR", "user_id": "300", "action": "login_failed", "details": "Account suspended"},
    {"timestamp": "2024-04-26 11:40:22", "level": "INFO", "user_id": "42", "action": "admin_action", "details": "Updated subscription for user 200"},
]


def _api_get(endpoint: str, params: dict = None):
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json(), True
    except Exception:
        return None, False


def _api_post(endpoint: str, data: dict = None):
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.post(url, json=data, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json(), True
    except Exception:
        return None, False


def _api_delete(endpoint: str):
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.delete(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json(), True
    except Exception:
        return None, False


def get_prices():
    data, ok = _api_get("/api/v1/prices")
    if ok and data:
        return data, True
    return MOCK_PRICES, False


def get_user(user_id: str):
    data, ok = _api_get(f"/api/v1/user/{user_id}")
    if ok and data:
        return data, True
    user = MOCK_USERS.get(str(user_id))
    return user, False


def get_portfolio(user_id: str):
    data, ok = _api_get("/api/v1/portfolio", params={"user_id": user_id})
    if ok and data:
        return data, True
    return MOCK_PORTFOLIO, False


def add_portfolio_item(user_id: str, symbol: str, amount: float, avg_buy_price: float):
    data, ok = _api_post("/api/v1/portfolio", data={
        "user_id": user_id, "symbol": symbol,
        "amount": amount, "avg_buy_price": avg_buy_price
    })
    return ok


def get_alerts(user_id: str):
    data, ok = _api_get("/api/v1/alerts", params={"user_id": user_id})
    if ok and data:
        return data, True
    return MOCK_ALERTS, False


def create_alert(user_id: str, symbol: str, condition: str, target_price: float):
    data, ok = _api_post("/api/v1/alerts", data={
        "user_id": user_id, "symbol": symbol,
        "condition": condition, "target_price": target_price
    })
    return ok


def delete_alert(alert_id: str):
    _, ok = _api_delete(f"/api/v1/alerts/{alert_id}")
    return ok


def get_transactions(user_id: str):
    data, ok = _api_get("/api/v1/history", params={"user_id": user_id})
    if ok and data:
        return data, True
    return MOCK_TRANSACTIONS, False


def get_reports_subscription(user_id: str):
    data, ok = _api_get(f"/api/v1/reports/subscription", params={"user_id": user_id})
    if ok and data:
        return data, True
    return {"subscribed": False, "email": "", "frequency": "daily"}, False


def update_reports_subscription(user_id: str, subscribed: bool, email: str, frequency: str):
    _, ok = _api_post("/api/v1/reports/subscription", data={
        "user_id": user_id, "subscribed": subscribed,
        "email": email, "frequency": frequency
    })
    return ok


def get_system_status():
    data, ok = _api_get("/api/v1/admin/system-status")
    if ok and data:
        return data, True
    return MOCK_SYSTEM_STATUS, False


def get_all_users():
    data, ok = _api_get("/api/v1/admin/users")
    if ok and data:
        return data, True
    return MOCK_USERS_LIST, False


def get_logs():
    data, ok = _api_get("/api/v1/admin/logs")
    if ok and data:
        return data, True
    return MOCK_LOGS, False


def delete_user_data(user_id: str):
    _, ok = _api_delete(f"/api/v1/user/{user_id}/data")
    return ok


def generate_portfolio_history(portfolio: list, prices: list) -> pd.DataFrame:
    price_map = {p["symbol"]: p["price"] for p in prices}
    dates = [datetime.now() - timedelta(days=i) for i in range(30, -1, -1)]
    records = []
    for date in dates:
        total_value = 0
        factor = 1 + random.uniform(-0.02, 0.02)
        for item in portfolio:
            symbol = item["symbol"]
            current_price = price_map.get(symbol, 0)
            historical_price = current_price * (0.85 + random.uniform(0, 0.3)) * factor
            total_value += item["amount"] * historical_price
        records.append({"date": date.strftime("%Y-%m-%d"), "value": round(total_value, 2)})
    return pd.DataFrame(records)
