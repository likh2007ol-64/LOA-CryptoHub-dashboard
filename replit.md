# Workspace

## Overview

pnpm workspace monorepo using TypeScript. Each package manages its own dependencies. Also includes a Python Streamlit crypto dashboard.

## Stack

- **Monorepo tool**: pnpm workspaces
- **Node.js version**: 24
- **Package manager**: pnpm
- **TypeScript version**: 5.9
- **API framework**: Express 5
- **Database**: PostgreSQL + Drizzle ORM
- **Validation**: Zod (`zod/v4`), `drizzle-zod`
- **API codegen**: Orval (from OpenAPI spec)
- **Build**: esbuild (CJS bundle)
- **Python**: 3.11 (Streamlit dashboard)

## Key Commands

- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- `pnpm --filter @workspace/api-server run dev` — run API server locally

See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details.

## LOA-CryptoHub Dashboard

Streamlit-based crypto monitoring dashboard at `loa-crypto-dashboard/`.

### Structure
```
loa-crypto-dashboard/
├── app.py                    # Main page (home + top-10 prices)
├── pages/
│   ├── 1_Портфель.py         # Portfolio management + P&L
│   ├── 2_История.py          # Transaction history
│   ├── 3_Уведомления.py      # Price alerts
│   ├── 4_Отчёты.py           # Report subscriptions
│   ├── 5_Безопасность.py     # Security + session management
│   ├── 6_Админ_панель.py     # Admin panel (admin only)
│   ├── 7_Мониторинг.py       # System monitoring (admin only)
│   ├── 8_Кошельки.py         # Wallet management
│   ├── 9_AI_сигналы.py       # AI signals
│   ├── 10_DeFi.py            # DeFi analytics (TVL, APY, Gas)
│   └── 11_Экспорт.py         # CSV export
├── utils/
│   ├── api_client.py         # API integration (connects to external API)
│   └── theme_manager.py      # Theme management (Dark/Light/Neon/Blue)
└── .streamlit/config.toml    # Streamlit config (port 5000, headless, 0.0.0.0)
```

### Environment Variables
- `API_BASE_URL` — Backend API URL (default: `http://153.80.184.34`)

### Auth
- Login is via VK ID (text input), no Replit Auth — external backend handles user lookup

### Workflow
- Name: `LOA-CryptoHub Dashboard`
- Command: `cd loa-crypto-dashboard && streamlit run app.py --server.port 5000 --server.address 0.0.0.0 --server.headless true`
- Port: 5000 (webview)

### Notes
- App runs in demo mode when the external API at `http://153.80.184.34` is unreachable
- No Replit integrations needed — all data flows through the external backend API
