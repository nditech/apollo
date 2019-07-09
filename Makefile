compile:
	pip-compile --generate-hashes --no-index --no-emit-trusted-host --output-file=requirements/prod.txt requirements/prod.in
	pip-compile --generate-hashes --no-index --no-emit-trusted-host --output-file=requirements/dev.txt requirements/dev.in
babel:
	pybabel compile -d apollo/translations/
