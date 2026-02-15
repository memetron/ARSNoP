.PHONY: dev api web install-web test lint typecheck

# Start both the Flask API and Vite dev server
dev: api web

# Start the Flask REST API on port 5001
api:
	uv run python -m rest.app &

# Start the Vite dev server (proxies /api to Flask)
web:
	cd web && npm run dev

# Install frontend dependencies
install-web:
	cd web && npm install

# Run the test suite
test:
	uv run -m pytest test/ -q

# Lint Python sources
lint:
	uv run ruff check src/ test/ rest/

# Type-check Python sources
typecheck:
	uv run pyright src/
