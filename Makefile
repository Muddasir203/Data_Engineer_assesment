PY := python3
VENV := .venv
ACT := source $(VENV)/bin/activate

.PHONY: venv install etl analysis run test clean

venv:
	$(PY) -m venv $(VENV)
	@echo "Run: source $(VENV)/bin/activate"

install:
	pip install -r requirements.txt

etl:
	$(PY) -m src.etl

analysis:
	$(PY) analysis.py

run: etl analysis

test:
	pytest -q

clean:
	rm -f nyc311.sqlite
	rm -rf outputs 