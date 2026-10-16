.PHONY: help venv install db-up db-down gen load evm train score pipeline compose-up compose-down test bench evm-validate k8s-up k8s-down web

help:
	@echo "CCPIP platform targets:"
	@echo "  install       Install Python deps into .venv"
	@echo "  db-up         Start local Postgres (docker)"
	@echo "  gen           Generate synthetic dataset -> datagen/out"
	@echo "  load          Load generated CSVs via ingestion API"
	@echo "  evm           Compute EVM KPI rows"
	@echo "  train         Train + compare delay-risk models (Table II)"
	@echo "  score         Score activities with the trained model"
	@echo "  pipeline      Full local pipeline (db+gen+load+evm+train+score)"
	@echo "  compose-up    Full stack via docker compose (ends on E2E verify)"
	@echo "  test          Run unit tests"
	@echo "  bench         Reproduce Table II benchmark"
	@echo "  evm-validate  Validate EVM outputs in the DB"
	@echo "  web           Run the web UI locally (http://localhost:8080)"
	@echo "  k8s-up        Deploy to Kubernetes (kustomize)"
	@echo "  k8s-down      Remove Kubernetes resources"

install:
	python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

db-up:
	docker run -d --name ccpip-pg -e POSTGRES_USER=ccpip -e POSTGRES_PASSWORD=ccpip -e POSTGRES_DB=ccpip -p 5432:5432 postgres:16-alpine

db-down:
	docker rm -f ccpip-pg

gen:
	.venv/bin/python -m datagen.generate --out datagen/out

load:
	.venv/bin/python -m datagen.load --in datagen/out --api http://localhost:8000

evm:
	.venv/bin/python -m services.analytics.app.worker

train:
	.venv/bin/python -m services.risk.app.train --data datagen/out/risk_training.csv

score:
	.venv/bin/python -m services.risk.app.score

compose-up:
	docker compose up --abort-on-container-exit --exit-code-from pipeline

compose-down:
	docker compose down -v

test:
	.venv/bin/pytest -q

bench:
	.venv/bin/python -m eval.benchmark_models --out eval/output

evm-validate:
	.venv/bin/python -m eval.validate_evm --out eval/output

k8s-up:
	kubectl apply -k k8s/

k8s-down:
	kubectl delete -k k8s/ --ignore-not-found

web:
	.venv/bin/uvicorn services.web.app.main:app --host 0.0.0.0 --port 8080
