.PHONY: help up down logs ps restart clean \
        dev-backend dev-frontend dev-bridge dev-worker \
        backend-shell migrate revision \
        seed-synthetic build-dataset train eval \
        test lint format \
        install-backend install-frontend install-bridge install-ml install-all

help:
	@echo "Gaia AI - common commands"
	@echo ""
	@echo "Infra:"
	@echo "  make up               # Start all docker services"
	@echo "  make down             # Stop all services"
	@echo "  make logs             # Tail all logs"
	@echo "  make ps               # Show running services"
	@echo "  make restart svc=X    # Restart one service"
	@echo "  make clean            # Stop + remove volumes (DATA LOSS)"
	@echo ""
	@echo "Dev (run individual services with hot reload outside docker):"
	@echo "  make dev-backend      # FastAPI on :8000"
	@echo "  make dev-frontend     # Next.js on :3000"
	@echo "  make dev-bridge       # WhatsApp bridge on :4000"
	@echo "  make dev-worker       # Celery worker"
	@echo ""
	@echo "Backend:"
	@echo "  make migrate          # Run alembic upgrade head"
	@echo "  make revision m=msg   # Create new migration"
	@echo "  make backend-shell    # Shell inside backend container"
	@echo ""
	@echo "ML / Research:"
	@echo "  make seed-synthetic n=10   # Generate N synthetic users"
	@echo "  make build-dataset         # Build train/val/test jsonl"
	@echo "  make train                 # Run QLoRA training (needs cloud GPU)"
	@echo "  make eval                  # Run full evaluation pipeline"
	@echo ""
	@echo "Quality:"
	@echo "  make test             # Backend tests"
	@echo "  make lint             # Lint all"
	@echo "  make format           # Format all"

# ----- Infra ---------------------------------------------------------------
up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

ps:
	docker compose ps

restart:
	docker compose restart $(svc)

clean:
	docker compose down -v

# ----- Dev (local outside docker) -----------------------------------------
dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

dev-bridge:
	cd whatsapp-bridge && npm run dev

dev-worker:
	cd backend && celery -A app.workers.celery_app.celery_app worker --loglevel=INFO

# ----- Backend -------------------------------------------------------------
backend-shell:
	docker compose exec backend bash

migrate:
	docker compose exec backend alembic upgrade head

revision:
	docker compose exec backend alembic revision --autogenerate -m "$(m)"

# ----- ML / Research -------------------------------------------------------
n ?= 10
seed-synthetic:
	cd ml && python -m synthetic.generate_personas --n $(n)
	cd ml && python -m synthetic.generate_histories
	cd ml && python -m synthetic.generate_pairs

build-dataset:
	cd ml && python -m dataset.build_jsonl

train:
	cd ml && python -m train.train_qlora

eval:
	cd ml && python -m eval.run_all

# ----- Quality -------------------------------------------------------------
test:
	cd backend && pytest -q

lint:
	cd backend && ruff check app
	cd frontend && npm run lint

format:
	cd backend && ruff format app
	cd frontend && npm run format

# ----- Install -------------------------------------------------------------
install-backend:
	cd backend && pip install -e ".[dev]"

install-frontend:
	cd frontend && npm install

install-bridge:
	cd whatsapp-bridge && npm install

install-ml:
	cd ml && pip install -e .

install-all: install-backend install-frontend install-bridge install-ml
