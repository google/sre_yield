PYTHON?=python
NOSETESTS?=nosetests
TESTOPTS?=
FLAKE8?=flake8
RST2HTML?=rst2html
PYGMENTIZE?=pygmentize
SOURCES=sre_yield setup.py

.PHONY: all
all:

.PHONY: setup
setup:
	$(PYTHON) -m pip install -Ur requirements-dev.txt

.PHONY: doctest
doctest: README.rst
	$(PYTHON) -m doctest $<

.PHONY: test
test:
	$(PYTHON) -m coverage run -m sre_yield.tests $(TESTOPTS)
	$(PYTHON) -m coverage report

.PHONY: lint
lint:
	$(FLAKE8) $(SOURCES)

.PHONY: clean
clean:
	find sre_yield -name '*.py[co]' -delete

pygments.css:
	$(PYGMENTIZE) -S emacs -f html > $@

%.html: %.rst pygments.css
	$(RST2HTML) --stylesheet=/usr/share/docutils/writers/html4css1/html4css1.css,pygments.css $< > $@

.PHONY: bench
bench:
	PYTHON=$(PYTHON) ./benchmarks/bench.sh

.PHONY: format
format:
	isort --recursive -y sre_yield benchmarks setup.py
	black sre_yield benchmarks setup.py

.PHONY: release
release:
	rm -rf dist
	$(PYTHON) setup.py sdist bdist_wheel
	twine upload dist/*
