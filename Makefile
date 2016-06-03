.PHONY: help init tests test cov docs doc

help:
	@cat make-help.md

init:
	pip install -r requirements.txt

tests: test
test:
	py.test --pylint arrowhead tests

cov:
	py.test --cov=arrowhead --cov-report=html --cov-report=term arrowhead tests
	xdg-open coverage_report_html/index.html

docs: doc
doc:
	$(MAKE) -C docs html
