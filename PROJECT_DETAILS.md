# Secure Chat Demo — Extended Documentation

## Overview
Secure Chat Demo is a FastAPI-based web application that implements a simple group chat with authentication, WebSockets, and optional TLS. The project aims to demonstrate differences between HTTP and HTTPS, and a pragmatic setup for secure real-time messaging while keeping the code approachable.

## Architecture
- FastAPI app (`app/`) with two routers: auth and chat
- Frontend is server-rendered Jinja2 templates with a small vanilla JS client (`static/js/chat.js`)
- WebSockets for real-time chat and lightweight notifications
- Two SQLite databases under `data/`:
  - `users.sqlite3` (UsersBase): authentication data
  - `chat.sqlite3` (ChatBase): groups, memberships, messages
  Cross-database foreign keys are not enforced; IDs are resolved at runtime across sessions.

## Data Model
- Users (UsersBase)
  - id, username, password_hash, created_at
- Chat (ChatBase)
  - Group: id, name, created_at
  - Membership: id, user_id (int), group_id (FK groups), joined_at
  - Message: id, group_id (FK groups), author_id (int), content, created_at

Note: `Membership.user_id` and `Message.author_id` are integers referencing users DB; cross-DB FK constraints are not possible in SQLite. The app resolves usernames by querying the users DB.

## Key Features
- Auth: registration, login with session cookie
- Realtime chat per group (WebSocket `/ws/chat/{group_id}`)
- Active users (global and per-group), showing client IPs when available
- Message timestamps (HH:MM:SS)
- Independent scrollable message area
- Live group list updates via notification WebSocket (`/ws`) without page reload
- Automatic static asset versioning per startup; override via `ASSET_VERSION`
- TLS support with self-signed cert stored in `.tls/`

## Configuration
- TLS config: `tls_config.json`
- Runtime flags (run.py):
  - `--host`, `--port`
  - `--tls` to enable HTTPS
  - `--certfile`, `--keyfile` (default `.tls/cert.pem`, `.tls/key.pem`)
  - `--tls-config`
- Environment variables:
  - `ASSET_VERSION` to pin asset version for cache-busting

## Startup Flow
- `app/main.py` creates the FastAPI app
- Static files mounted at `/static`
- `init_db()` creates both databases and tables under `data/`
- Asset version set at startup (UTC timestamp or `ASSET_VERSION`)

## WebSocket Behavior
- Chat WS authenticates via session cookie; users are mapped to sockets
- Broadcasting supports per-group delivery; disconnects clean up mappings
- Notification WS is separate and used for out-of-band events (new groups)

## Security Notes
- Cookies: `httponly`, `samesite=lax` (consider `Secure` under HTTPS)
- Self-signed TLS for development only; use proper certificates in production
- Session store is in-memory; use persistent storage (e.g., Redis) in production

## Development Tips
- Hard refresh after code changes (Ctrl+Shift+R) if asset versioning disabled
- Check `data/` directory for the two SQLite files
- Logs: `server.log` (if used), update `.gitignore` as needed

## Future Enhancements
- Replace in-memory sessions with Redis
- Add presence updates via WS (server push on join/leave for active users list)
- Add pagination and message editing/deletion
- Migrate to Postgres with proper cross-database constraints (or unify schemas)

## License
MIT
