# Anchor

Personal dashboard PWA for focus, habits, and content. Built for one user (me), designed to be accessed from my phone. Design inspired by Linear and Notion — calm, minimal, grayscale, every pixel earns its space.

## Features

- **Home** — weather, daily priority, pomodoro timer, journal, daily fact
- **Feed** — Hacker News, YouTube, RSS feeds, reading queue
- **Todos** — swipe gestures, iOS Reminders-style animations, haptic feedback
- **Track** — sleep, workouts, mood, water, custom habits, streaks, weekly reviews
- **Note** — quick capture to journal from any screen

## Stack

SvelteKit + TypeScript frontend, Python + FastAPI + SQLite backend. Content pulled via yt-dlp, feedparser, httpx. Push notifications via Web Push.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and [bun](https://bun.sh/).

```bash
make dev          # run backend + frontend
make build        # build frontend for production
make run          # production server (HTTP)
```

Database auto-creates at `data/base.db` on first run.

## Deploy to Fly.io

The easiest way to run Anchor on your phone without keeping a laptop on. Fly handles HTTPS, so no mkcert or cert management needed. Costs under $1/month with auto-stop, or ~$2/month always-on.

### First-time setup

1. Install the [Fly CLI](https://fly.io/docs/flyctl/install/) and sign up:

```bash
brew install flyctl
fly auth signup
```

2. Pick a unique app name, update `app` in `fly.toml` to match, then create the app and a 1GB persistent volume:

```bash
fly apps create your-app-name
fly volumes create anchor_data --region dfw --size 1
```

3. Build the frontend locally and deploy:

```bash
make build
fly deploy
```

Your app is live at `https://your-app-name.fly.dev`.

### Subsequent deploys

```bash
make build && fly deploy
```

### Optional: YouTube cookies

YouTube scraping requires browser cookies. Upload them to the volume:

```bash
fly ssh console
cat > /data/yt_cookies.txt << 'EOF'
(paste Netscape-format cookies here)
EOF
```

### Optional: GitHub contributions

Enter your GitHub username and personal access token in the Settings page. Stored in the database, persists across deploys.

### Auto-stop behavior

By default, the machine stops when idle and starts on the first request (~1-2s cold start). This keeps costs near zero. Content is fetched fresh on each startup.

To keep the machine always on (so the 8am/6pm scheduled fetches and push notifications work reliably), set `min_machines_running = 1` in `fly.toml`.

### Adding it as an app on iPhone

1. Open `https://your-app-name.fly.dev` in Safari
2. Tap the share button -> "Add to Home Screen"
3. It launches as a full-screen app with no browser chrome

## Alternative: run locally with Tailscale

If you'd rather run it off your own machine, install [Tailscale](https://tailscale.com/) on your laptop and phone. The backend runs on your laptop and is accessible over Tailscale's private network — no port forwarding, no public server.

Push notifications over Tailscale require HTTPS, which means generating local certs:

1. Install [mkcert](https://github.com/FiloSottile/mkcert) and run `mkcert -install`
2. Generate certs: `mkcert your-tailscale-ip` and move them to `backend/cert.crt` and `backend/cert.key`
3. On iPhone, AirDrop the root CA from `$(mkcert -CAROOT)/rootCA.pem`, install and trust it in Settings
4. Run `make build && make run-https`

The downside: the app is only available when your laptop is on.

## License

Personal project. Feel free to look around or fork it.
