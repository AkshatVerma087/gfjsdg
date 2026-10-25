.PHONY: up down test lint fmt ingest check

up:
	docker compose up -d

down:
	docker compose down

test:
	cd backend && pytest -q
	cd frontend && npm test

lint:
	cd backend && ruff check .
	cd frontend && npm run lint

fmt:
	cd backend && ruff format .
	cd frontend && npx prettier --write "src/**/*.{js,jsx,css}"

check:
	cd backend && python manage.py check

ingest:
	cd backend && python manage.py ingest_wind
