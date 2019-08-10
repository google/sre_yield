PYTHON?=python
NOSETESTS?=nosetests
TESTOPTS?=-v
PYLINT?=pylint
RST2HTML?=rst2html
PYGMENTIZE?=pygmentize

.PHONY: all
all:

.PHONY: doctest
doctest: README.rst
	$(PYTHON) -m doctest $<

.PHONY: test
test:
	@$(NOSETESTS) --with-doctest --doctest-extension=rst $(TESTOPTS)

.PHONY: coverage
coverage:
	@$(NOSETESTS) --with-doctest --doctest-extension=rst --with-coverage --cover-package=sre_yield --cover-html --cover-html-dir=coverage

.PHONY: lint
lint:
	$(PYLINT) *.py sre_yield/*.py

.PHONY: clean
clean:
	rm -f *.py[co]

pygments.css:
	$(PYGMENTIZE) -S emacs -f html > $@

%.html: %.rst pygments.css
	$(RST2HTML) --stylesheet=/usr/share/docutils/writers/html4css1/html4css1.css,pygments.css $< > $@

.PHONY: bench
bench:
	PYTHON=$(PYTHON) ./benchmarks/bench.sh
