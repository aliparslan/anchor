BUN := $(shell which bun)

.PHONY: dev dev-backend dev-frontend build run clean

# Development: run backend and frontend concurrently
dev:
	@echo "Starting backend and frontend..."
	@make dev-backend & make dev-frontend

dev-backend:
	cd backend && uv run uvicorn main:app --reload --port 8000

dev-frontend:
	cd frontend && $(BUN) run dev --port 5173

# Build frontend for production
build:
	cd frontend && $(BUN) run build

# Run production server (serves built frontend + API)
run:
	cd backend && uv run uvicorn main:app --host 0.0.0.0 --port 8000

# Run with HTTPS (required for push notifications)
# First: mkcert -install, then make build, then make run-https
# On phone: install the mkcert root CA (see README)
run-https:
	cd backend && uv run uvicorn main:app --host 0.0.0.0 --port 8443 \
		--ssl-certfile cert.crt --ssl-keyfile cert.key

clean:
	rm -rf frontend/build frontend/.svelte-kit data/base.db
