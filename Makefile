install:
	python -m pip install -r requirements.txt

test:
	python -m pytest tests/unit tests/integration tests/e2e

coverage:
	python -m pytest --cov=src --cov-branch --cov-report=term-missing --cov-report=xml:coverage.xml --cov-report=html:htmlcov --cov-fail-under=85

lint:
	python -m ruff check src tests

run:
	python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
