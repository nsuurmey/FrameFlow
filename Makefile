.PHONY: check lint test typecheck clean install

# Run all checks (linting, tests, type checking)
check: lint test typecheck
	@echo "✓ All checks passed!"

# Run linting with ruff
lint:
	@echo "Running ruff linter..."
	ruff check src/ tests/

# Run tests with pytest
test:
	@echo "Running pytest..."
	python -m pytest tests/

# Run type checking with mypy
typecheck:
	@echo "Running mypy type checker..."
	mypy src/clarity

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .coverage htmlcov/

# Install package in editable mode
install:
	pip install -e .

# Install dev dependencies
install-dev:
	pip install -e ".[dev]"
