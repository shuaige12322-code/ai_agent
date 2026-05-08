.PHONY: help setup install run test lint format clean docker-build docker-run

help:
	@echo "AI Agent - Available Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup          - Setup virtual environment and install dependencies"
	@echo "  make install        - Install dependencies only"
	@echo ""
	@echo "Running:"
	@echo "  make run            - Run the server"
	@echo "  make test           - Run tests"
	@echo ""
	@echo "Development:"
	@echo "  make lint           - Run code linting"
	@echo "  make format         - Format code with black"
	@echo "  make clean          - Clean up generated files"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-run     - Run Docker container"

setup:
	python3 -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	cp .env.example .env
	mkdir -p data/memories data/vectors logs
	@echo "✓ Setup completed! Edit .env file and add your CLAUDE_API_KEY"

install:
	pip install -r requirements.txt

run:
	python server.py

test:
	python test.py

lint:
	flake8 app --max-line-length=100
	mypy app --ignore-missing-imports

format:
	black app --line-length=100
	isort app

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".mypy_cache" -delete
	rm -rf build dist *.egg-info

docker-build:
	docker build -t ai-agent:latest .

docker-run:
	docker run -p 8000:8000 \
		-e CLAUDE_API_KEY=${CLAUDE_API_KEY} \
		-v $(PWD)/data:/app/data \
		ai-agent:latest
