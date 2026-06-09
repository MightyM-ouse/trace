.PHONY: help init dev server ui install test lint clean

help:
	@echo "TRACE — make targets"
	@echo "  make init     Interactive project setup wizard"
	@echo "  make install  Install backend + frontend deps"
	@echo "  make dev      Run FastAPI (:8000) and Vite dashboard (:5173)"
	@echo "  make server   Run only the FastAPI telemetry server"
	@echo "  make ui       Run only the Vite dashboard"
	@echo "  make test     Run backend + frontend tests"
	@echo "  make lint     Run ruff + eslint"
	@echo "  make clean    Remove local telemetry + build artifacts"

init:
	bash scripts/setup.sh

install:
	python3 -m pip install -r src/server/requirements.txt
	cd src/ui && npm install

server:
	cd src/server && python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

ui:
	cd src/ui && npm run dev

dev:
	@echo "Starting FastAPI (:8000) and Vite (:5173)..."
	@( cd src/server && python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload & ) ; \
	  cd src/ui && npm run dev

test:
	python3 -m pytest -q
	cd src/ui && npm test --silent

lint:
	ruff check src/server tests
	cd src/ui && npx eslint src

clean:
	rm -f agent-logs/*.db agent-logs/*.db-wal agent-logs/*.db-shm agent-logs/*.jsonl
	rm -rf src/ui/dist src/ui/node_modules src/server/__pycache__
