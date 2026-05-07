.PHONY: install test lint bench demo clean

install:
	pip install -r requirements.txt

test:
	pytest sage/tests

lint:
	ruff check .
	mypy --strict sage/
	bandit -r sage/

bench:
	python -m sage.benchmarks.compare_single_vs_sage

demo:
	python demos/demo_sage_pro.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .venv .mypy_cache .pytest_cache .ruff_cache htmlcov .coverage
