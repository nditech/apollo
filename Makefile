pip-compile:
	pip-compile --generate-hashes --no-index --no-emit-trusted-host --output-file=requirements/prod.txt requirements/prod.in
	pip-compile --generate-hashes --no-index --no-emit-trusted-host --output-file=requirements/dev.txt requirements/dev.in
babel-compile:
	pybabel compile -d apollo/translations/
parser:
	canopy apollo/resources/parser/quality.peg --javascript
	mv apollo/resources/parser/quality.js apollo/static/js/
