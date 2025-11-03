# Secure Chat Demo (HTTP vs HTTPS)

A minimal chat web app showcasing differences between HTTP and HTTPS, with optional TLS using a self-signed certificate.

Features:
- User registration and login (session cookie)
- Create and join group chats
- Real-time messaging via WebSockets
- Active users overall and per current group (shows IPs where available)
- Message timestamps (HH:MM:SS)
- Independent scrollable messages area (header stays visible)
- Light/Dark theme UI
- CLI flags to run over HTTP or HTTPS
- Automatic cache-busting for static assets (asset_version; override via `ASSET_VERSION`)
- TLS (HTTPS) with self-signed certificate (stored under `tls/`) controlled by `tls_config.json`
- Live group list updates without reloading the page

## Quickstart

1) Create a Python venv and install deps

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Run over plain HTTP (default port 8000)

```bash
python run.py --port 8000
```

3) Run over HTTPS with self-signed TLS

```bash
python run.py --tls --port 8443 --certfile .tls/cert.pem --keyfile .tls/key.pem --tls-config tls_config.json
```

Open in browser:
- HTTP:  http://127.0.0.1:8000
- HTTPS: https://127.0.0.1:8443 (accept the self-signed certificate warning)

## What changes between HTTP and HTTPS?
- Transport security: HTTPS encrypts requests, responses, and WebSocket traffic (wss://), preventing sniffing and tampering.
- Cookies: With HTTPS, you can set `Secure` cookies so they’re never sent over HTTP. This demo uses `httponly` and `samesite=lax` by default.
- Mixed content: Browsers block `ws://` from HTTPS origins; we automatically use `wss://` when on HTTPS.

## Notes
- Storage uses two separate SQLite databases under `data/`:
	- `data/users.sqlite3` (users and credentials)
	- `data/chat.sqlite3` (groups, memberships, messages)
	The folder is auto-created on startup.
- TLS files default to `tls/cert.pem` and `tls/key.pem`. If missing and `--tls` is enabled, a self-signed cert is generated based on `tls_config.json`.
- Active users are tracked by WebSocket connections; we also expose per-group active users and display client IPs when available.
- Static assets are versioned each startup (UTC timestamp). Override with `ASSET_VERSION=...` if needed.
- For production, use a persistent session store (e.g., Redis) and secure cookies with a fixed secret.

## Live updates without reload
When a user creates a new group, other clients receive a `new_group:` notification via a dedicated WebSocket and refresh the group list in-place (the current chat remains open).

## License
MIT