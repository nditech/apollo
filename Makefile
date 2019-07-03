compile:
	pip-compile --generate-hashes --no-index --output-file=requirements/prod.txt requirements/prod.in
	pip-compile --generate-hashes --no-index --output-file=requirements/dev.txt requirements/dev.in
