codegen:
	openapi-python-generator openapi/payments.yaml app/clients --name payments_client
fix-imports:
	ruff check --select I --fix app/clients
lint:
	ruff check .
