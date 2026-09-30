SHELL := /bin/bash
# =============================================================================
# Variables
# =============================================================================

.DEFAULT_GOAL:=help
.ONESHELL:
USING_PDM		          	=	$(shell grep "tool.pdm" pyproject.toml && echo "yes")
USING_NPM             		= $(shell python3 -c "if __import__('pathlib').Path('package-lock.json').exists(): print('yes')")
ENV_PREFIX		        	=.venv/bin/
VENV_EXISTS           		=	$(shell python3 -c "if __import__('pathlib').Path('.venv/bin/activate').exists(): print('yes')")
NODE_MODULES_EXISTS			=	$(shell python3 -c "if __import__('pathlib').Path('node_modules').exists(): print('yes')")
SRC_DIR               		=src
BUILD_DIR             		=dist
PDM_OPTS 		          	?=
PDM 			            ?= 	pdm $(PDM_OPTS)

.EXPORT_ALL_VARIABLES:

ifndef VERBOSE
.SILENT:
endif


.PHONY: help
help: 		   										## Display this help text for Makefile
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)


.PHONY: upgrade
upgrade:       										## Upgrade all dependencies to the latest stable versions
	@echo "=> Updating all dependencies"
	@if [ "$(USING_PDM)" ]; then $(PDM) update; fi
	@echo "=> Python Dependencies Updated"
	@if [ "$(USING_NPM)" ]; then npm upgrade --latest; fi
	@echo "=> Node Dependencies Updated"
	@$(ENV_PREFIX)pre-commit autoupdate
	@echo "=> Updated Pre-commit"

.PHONY: uninstall
uninstall:
	@echo "=> Uninstalling PDM"
ifeq ($(OS),Windows_NT)
	@echo "=> Removing PDM from %APPDATA%\Python\Scripts"
	@if exist "%APPDATA%\Python\Scripts\pdm" (del "%APPDATA%\Python\Scripts\pdm")
else
	@echo "=> Removing PDM from ~/.local/bin"
	@rm -f ~/.local/bin/pdm
endif
	@echo "=> PDM removal complete"
	@echo "=> Uninstallation complete!"

# =============================================================================
# Developer Utils
# =============================================================================
install-pdm: 										## Install latest version of PDM
	@curl -sSLO https://pdm.fming.dev/install-pdm.py && \
	curl -sSL https://pdm.fming.dev/install-pdm.py.sha256 | shasum -a 256 -c - && \
	python3 install-pdm.py

install:											## Install the project and
	@if ! $(PDM) --version > /dev/null; then echo '=> Installing PDM'; $(MAKE) install-pdm; fi
	@if [ "$(VENV_EXISTS)" ]; then echo "=> Removing existing virtual environment"; fi
	if [ "$(VENV_EXISTS)" ]; then $(MAKE) destroy-venv; fi
	if [ "$(VENV_EXISTS)" ]; then $(MAKE) clean; fi
	@if [ "$(NODE_MODULES_EXISTS)" ]; then echo "=> Removing existing node modules"; fi
	if [ "$(NODE_MODULES_EXISTS)" ]; then $(MAKE) destroy-node_modules; fi
	@if [ "$(USING_PDM)" ]; then $(PDM) config venv.in_project true && python3 -m venv --copies .venv && . $(ENV_PREFIX)/activate && $(ENV_PREFIX)/pip install --quiet -U wheel setuptools cython pip mypy nodeenv; fi
	@if [ "$(USING_PDM)" ]; then $(PDM) install -G:all; fi
	@echo "=> Install complete! Note: If you want to re-install re-run 'make install'"


clean: 												## Cleanup temporary build artifacts
	@echo "=> Cleaning working directory"
	@rm -rf .pytest_cache .ruff_cache .hypothesis build/ -rf dist/ .eggs/ .coverage coverage.xml coverage.json htmlcov/ .mypy_cache
	@find . -name '*.egg-info' -exec rm -rf {} +
	@find . -name '*.egg' -exec rm -f {} +
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +
	@find . -name '__pycache__' -exec rm -rf {} +
	@find . -name '.pytest_cache' -exec rm -rf {} +
	@find . -name '.ipynb_checkpoints' -exec rm -rf {} +

destroy-venv: 											## Destroy the virtual environment
	@echo "=> Cleaning Python virtual environment"
	@rm -rf .venv

destroy-node_modules: 											## Destroy the node environment
	@echo "=> Cleaning Node modules"
	@rm -rf node_modules

tidy: clean destroy-venv destroy-node_modules ## Clean up everything

migrations:       ## Generate database migrations
	@echo "ATTENTION: This operation will create a new database migration for any defined models changes."
	@while [ -z "$$MIGRATION_MESSAGE" ]; do read -r -p "Migration message: " MIGRATION_MESSAGE; done ;
	@$(ENV_PREFIX)app database make-migrations --autogenerate -m "$${MIGRATION_MESSAGE}"

.PHONY: migrate
migrate:          ## Generate database migrations
	@echo "ATTENTION: Will apply all database migrations."
	@$(ENV_PREFIX)app database upgrade

.PHONY: build
build:
	@echo "=> Building package..."
	@if [ "$(USING_PDM)" ]; then pdm build; fi
	@echo "=> Package build complete..."

.PHONY: refresh-lockfiles
refresh-lockfiles:                                 ## Sync lockfiles with requirements files.
	@pdm update --update-reuse --group :all

.PHONY: lock
lock:                                             ## Rebuild lockfiles from scratch, updating all dependencies
	@pdm update --update-eager --group :all

# =============================================================================
# Dev Server
# =============================================================================
# Shared host storage seen by the web app, the pack workers, and (via the
# /storage mount) the provider containers in the docalchemy repo.
STORAGE_HOST ?= /home/gaopeng/localstorage/docalchemy
PACK_WORKERS  = docling:8081 mineru:8082 opendataloader:8083 franken_ocr:8084

.PHONY: dev
dev:												## Start all services (infra, providers, workers, backend, frontend)
	@echo "=> Starting all services"
	@$(MAKE) dev-infra dev-providers
	@echo "=> Waiting for infrastructure to be healthy..."
	@until docker compose -p docalchemy1 -f docker-compose.infra.yml exec -T db pg_isready -U app 2>/dev/null; do sleep 1; done
	@$(MAKE) dev-workers dev-backend dev-frontend
	@sleep 2
	@echo ""
	@echo "  Backend:    http://localhost:8000"
	@echo "  Frontend:   http://localhost:5173"
	@echo ""
	@echo "  make dev-stop   to stop all services"

.PHONY: dev-infra
dev-infra:											## Start PostgreSQL & Redis
	@echo "=> Starting PostgreSQL & Redis"
	@mkdir -p $(STORAGE_HOST)
	@docker compose -p docalchemy1 -f docker-compose.infra.yml up -d db redis 2>/dev/null || \
		( echo "   Ports in use — stopping stale containers first..." && \
		  docker compose -p docalchemy1 -f docker-compose.infra.yml down 2>/dev/null; \
		  docker compose -p docalchemy1 -f docker-compose.infra.yml up -d db redis )

.PHONY: dev-providers
dev-providers:										## Start the provider containers (docalchemy repo)
	@echo "=> Starting provider containers"
	@cd ../docalchemy && STORAGE_PATH=$(STORAGE_HOST) docker compose up -d

.PHONY: dev-workers
dev-workers:										## Start Celery pack workers (one per provider, on the host)
	@echo "=> Starting pack workers (docling, mineru, opendataloader, franken_ocr)"
	@mkdir -p logs
	@for spec in $(PACK_WORKERS); do \
		pack_id=$${spec%%:*}; port=$${spec##*:}; \
		PACK_ID=$$pack_id \
		PROVIDER_URL=http://localhost:$$port \
		PACK_QUEUE=analysis.$$pack_id \
		REDIS_URL=redis://localhost:16377/0 \
		DATABASE_URL=postgresql+asyncpg://app:app@localhost:15433/app \
		STORAGE_ROOT_PATH=$(STORAGE_HOST) \
		STORAGE_HOST_ROOT=$(STORAGE_HOST) \
		STORAGE_PROVIDER_ROOT=/storage \
		PYTHONPATH=src \
		nohup $(ENV_PREFIX)celery -A app.infrastructure.workers.pack_worker worker \
			--queues=analysis.$$pack_id --loglevel=info --concurrency=1 --hostname="$$pack_id@%h" \
			> logs/worker_$$pack_id.log 2>&1 & \
		echo $$! > /tmp/docalchemy-worker-$$pack_id.pid; \
		echo "   $$pack_id  (pid $$!, logs: logs/worker_$$pack_id.log)"; \
	done

.PHONY: dev-workers-rebuild
dev-workers-rebuild: dev-workers					## Alias for dev-workers (pack workers need no image build)

.PHONY: dev-backend
dev-backend:										## Start the Litestar backend on port 8000
	@echo "=> Starting backend on port 8000"
	@mkdir -p logs
	@DATABASE_URL="postgresql+asyncpg://app:app@localhost:15433/app" \
	STORAGE_ROOT_PATH=$(STORAGE_HOST) \
	PYTHONPATH=src LITESTAR_APP=app.asgi:app \
	nohup $(ENV_PREFIX)litestar run --host 0.0.0.0 --port 8000 \
		> logs/backend.log 2>&1 & echo $$! > /tmp/docalchemy-backend.pid
	@echo "   pid $$(cat /tmp/docalchemy-backend.pid), logs: logs/backend.log"

.PHONY: dev-frontend
dev-frontend:										## Start the Vite frontend dev server on port 5173
	@echo "=> Starting frontend on port 5173"
	@mkdir -p logs
	@nohup pnpm dev > logs/frontend.log 2>&1 & echo $$! > /tmp/docalchemy-vite.pid
	@echo "   pid $$(cat /tmp/docalchemy-vite.pid), logs: logs/frontend.log"

.PHONY: dev-stop
dev-stop:											## Stop all dev services
	@echo "=> Stopping all services"
	@for pidfile in /tmp/docalchemy-*.pid; do \
		pid=$$(cat "$$pidfile" 2>/dev/null); \
		[ -n "$$pid" ] && kill -TERM -- -$$(ps -o pgid= -p $$pid | tr -d ' ') 2>/dev/null || true; \
		rm -f "$$pidfile"; \
	done
	docker compose -p docalchemy1 -f docker-compose.infra.yml down
	cd ../docalchemy && docker compose down
	@echo "=> All services stopped"

.PHONY: restart
restart:												## Restart app services (backend, workers, frontend); keeps DB/Redis up
	@echo "=> Restarting app services (backend, workers, frontend)"
	@for pidfile in /tmp/docalchemy-backend.pid /tmp/docalchemy-vite.pid /tmp/docalchemy-worker-*.pid; do \
		pid=$$(cat "$$pidfile" 2>/dev/null); \
		[ -n "$$pid" ] && kill -TERM -- -$$(ps -o pgid= -p $$pid | tr -d ' ') 2>/dev/null || true; \
		rm -f "$$pidfile"; \
	done
	@$(MAKE) dev-infra
	@echo "=> Waiting for infrastructure to be healthy..."
	@until docker compose -p docalchemy1 -f docker-compose.infra.yml exec -T db pg_isready -U app 2>/dev/null; do sleep 1; done
	@$(MAKE) dev-workers dev-backend dev-frontend
	@sleep 2
	@echo "=> Restart complete"

# =============================================================================
# Tests, Linting, Coverage
# =============================================================================
.PHONY: lint
lint: 												## Runs pre-commit hooks; includes ruff linting, codespell, black
	@echo "=> Running pre-commit process"
	@$(ENV_PREFIX)pre-commit run --all-files
	@echo "=> Pre-commit complete"

.PHONY: format
format: 												## Runs code formatting utilities
	@echo "=> Running pre-commit process"
	@$(ENV_PREFIX)ruff . --fix
	@echo "=> Pre-commit complete"

.PHONY: coverage
coverage:  											## Run the tests and generate coverage report
	@echo "=> Running tests with coverage"
	@$(ENV_PREFIX)pytest tests --cov=app
	@$(ENV_PREFIX)coverage html
	@$(ENV_PREFIX)coverage xml
	@echo "=> Coverage report generated"

.PHONY: test
test:  												## Run the tests
	@echo "=> Running test cases"
	@$(ENV_PREFIX)pytest tests
	@echo "=> Tests complete"

# =============================================================================
# Docs
# =============================================================================
.PHONY: docs-install
docs-install: 										## Install docs dependencies
	@echo "=> Installing documentation dependencies"
	@$(PDM) install -dG:docs
	@echo "=> Installed documentation dependencies"

docs-clean: 										## Dump the existing built docs
	@echo "=> Cleaning documentation build assets"
	@rm -rf docs/_build
	@echo "=> Removed existing documentation build assets"

docs-serve: docs-clean 								## Serve the docs locally
	@echo "=> Serving documentation"
	$(PDM_RUN_BIN) sphinx-autobuild docs docs/_build/ -j auto --watch src --watch docs --watch tests --watch CONTRIBUTING.rst --port 8002

docs: docs-clean 									## Dump the existing built docs and rebuild them
	@echo "=> Building documentation"
	@$(PDM_RUN_BIN) sphinx-build -M html docs docs/_build/ -E -a -j auto --keep-going
