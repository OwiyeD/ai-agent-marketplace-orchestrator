.PHONY: help install test lint format clean docker-up docker-down migrate seed

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	poetry install
	pre-commit install

test: ## Run tests
	poetry run pytest

test-cov: ## Run tests with coverage
	poetry run pytest --cov-report=html --cov-report=term

lint: ## Run linting
	poetry run flake8 src tests
	poetry run mypy src

format: ## Format code
	poetry run black src tests
	poetry run isort src tests

clean: ## Clean cache files
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/

docker-up: ## Start development environment
	docker-compose -f infrastructure/docker/docker-compose.yml up -d

docker-down: ## Stop development environment
	docker-compose -f infrastructure/docker/docker-compose.yml down

migrate: ## Run database migrations
	./scripts/migrate.sh

seed: ## Seed database with test data
	python scripts/seed_data.py

performance: ## Run performance tests
	poetry run locust -f tests/performance/test_load.py --headless -u 10 -r 2 -t 30s

setup: install docker-up migrate seed ## Complete development setup