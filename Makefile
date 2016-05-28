.PHONY: help init test cov doc

help:
	@cat make-help.md

init:
	pip install -r requirements.txt

test:
	py.test --pylint arrowhead

cov:
	py.test --cov=arrowhead --cov-report=html --cov-report=term
	xdg-open coverage_report_html/index.html

doc:
	@echo "Missing documentation!"
