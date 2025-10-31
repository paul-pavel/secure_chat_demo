# Secure Chat Demo (HTTP vs HTTPS)

A minimal chat web app showcasing differences between HTTP and HTTPS, with optional TLS using a self-signed certificate.

Features:
- User registration and login (session cookie)
- Create and join group chats
- Real-time messaging via WebSockets
- List of active users
- Light/Dark theme UI
- CLI flags to run over HTTP or HTTPS
- Self-signed cert generation controlled by `tls_config.json`

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
python run.py --tls --port 8443 --certfile cert.pem --keyfile key.pem --tls-config tls_config.json
```

Open in browser:
- HTTP:  http://127.0.0.1:8000
- HTTPS: https://127.0.0.1:8443 (accept the self-signed certificate warning)

## What changes between HTTP and HTTPS?
- Transport security: HTTPS encrypts requests, responses, and WebSocket traffic (wss://), preventing sniffing and tampering.
- Cookies: With HTTPS, you can set `Secure` cookies so they’re never sent over HTTP. This demo uses `httponly` and `samesite=lax` by default.
- Mixed content: Browsers block `ws://` from HTTPS origins; we automatically use `wss://` when on HTTPS.

## Notes
- This demo uses SQLite for storage. The DB file is created next to the project as `secure_chat.sqlite3`.
- Active users are tracked by open WebSocket connections and a simple in-memory session store.
- For production, use a persistent session store (Redis) and secure cookies with a fixed secret.

## License
MIT