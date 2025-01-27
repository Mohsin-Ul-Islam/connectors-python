.PHONY: test lint autoformat run ftest install dev release

PYTHON=python3.10
ARCH=$(shell uname -m)
PERF8?=no

bin/python:
	$(PYTHON) -m venv .
	bin/pip install --upgrade pip

install: bin/python
	bin/pip install -r requirements/$(ARCH).txt

dev: install
	bin/pip install -r requirements/tests.txt

bin/elastic-ingest: bin/python
	bin/pip install -r requirements/$(ARCH).txt
	bin/python setup.py develop

bin/black: bin/python
	bin/pip install -r requirements/$(ARCH).txt
	bin/pip install -r requirements/tests.txt
	

bin/pytest: bin/python
	bin/pip install -r requirements/$(ARCH).txt
	bin/pip install -r requirements/tests.txt

lint: bin/python bin/black bin/elastic-ingest
	bin/black --check connectors
	bin/black --check setup.py
	bin/flake8 connectors --exclude fixtures
	bin/flake8 setup.py
	bin/black --check scripts
	bin/flake8 scripts

autoformat: bin/python bin/black bin/elastic-ingest
	bin/black connectors
	bin/black setup.py
	bin/black scripts

test:	bin/pytest bin/elastic-ingest
	bin/pytest --cov-report term-missing --cov-report html --cov=connectors -sv connectors/tests connectors/sources/tests

release: install
	bin/python setup.py sdist

ftest: bin/pytest bin/elastic-ingest
	connectors/tests/ftest.sh $(NAME) $(PERF8)

run: install
	bin/elastic-ingest --debug
