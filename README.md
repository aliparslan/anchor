# Anchor

Personal dashboard PWA for focus, habits, and content. Built for one user (me), runs off my laptop, accessed from my phone over Tailscale. Design inspired by Linear and Notion — calm, minimal, grayscale, every pixel earns its space.

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
make build        # build frontend
make run          # production server
make run-https    # production with HTTPS (needs mkcert certs)
```

Database auto-creates at `data/base.db` on first run.

## How I run it

The backend runs on my laptop at home. I use [Tailscale](https://tailscale.com/) to access it from my phone over a private network — no port forwarding, no public server.

### Adding it as an app on iPhone

1. Open the app URL in Safari (e.g. `https://100.x.x.x:8443`)
2. Tap the share button → "Add to Home Screen"
3. It launches as a full-screen app with no browser chrome

### Push notifications

Push notifications require HTTPS. Here's how to set it up:

1. Install [mkcert](https://github.com/FiloSottile/mkcert) and run `mkcert -install` to create a local CA
2. Generate certs: `mkcert your-tailscale-ip` and move them to `backend/cert.crt` and `backend/cert.key`
3. On your iPhone, AirDrop yourself the root CA file from `$(mkcert -CAROOT)/rootCA.pem`
4. Install the profile in Settings → General → VPN & Device Management, then trust it in Settings → General → About → Certificate Trust Settings
5. Run `make build && make run-https`
6. Open the app and enable notifications when prompted — VAPID keys are auto-generated on first run

## License

Personal project. Feel free to look around or fork it.
