.PHONY: build up down restart logs migrate makemigrations createsuperuser shell test lint collectstatic celery-logs frontend-logs db-shell redis-cli clean

# ── Docker Compose ─────────────────────────────

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

# ── Backend ────────────────────────────────────

migrate:
	docker compose exec backend python manage.py migrate

makemigrations:
	docker compose exec backend python manage.py makemigrations

createsuperuser:
	docker compose exec backend python manage.py createsuperuser

shell:
	docker compose exec backend python manage.py shell

collectstatic:
	docker compose exec backend python manage.py collectstatic --noinput

test:
	docker compose exec backend python manage.py test

lint:
	docker compose exec backend python -m flake8 .
	cd frontend && npx eslint . || true

# ── Service Logs ───────────────────────────────

backend-logs:
	docker compose logs -f backend

frontend-logs:
	docker compose logs -f frontend

celery-logs:
	docker compose logs -f celery_worker celery_beat

db-logs:
	docker compose logs -f db

# ── Database ───────────────────────────────────

db-shell:
	docker compose exec db psql -U $${POSTGRES_USER:-tcchub} -d $${POSTGRES_DB:-tcchub}

redis-cli:
	docker compose exec redis redis-cli

db-backup:
	docker compose exec db pg_dump -U $${POSTGRES_USER:-tcchub} $${POSTGRES_DB:-tcchub} > backup_$$(date +%Y%m%d_%H%M%S).sql

db-restore:
	@test -n "$(FILE)" || (echo "Usage: make db-restore FILE=backup.sql" && exit 1)
	cat $(FILE) | docker compose exec -T db psql -U $${POSTGRES_USER:-tcchub} -d $${POSTGRES_DB:-tcchub}

# ── Cleanup ────────────────────────────────────

clean:
	docker compose down -v --remove-orphans
	docker system prune -f
