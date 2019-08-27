pip-compile:
	pip-compile --allow-unsafe --generate-hashes --no-index --no-emit-trusted-host --output-file=requirements/prod.txt requirements/prod.in
	pip-compile --allow-unsafe --generate-hashes --no-index --no-emit-trusted-host --output-file=requirements/dev.txt requirements/dev.in
babel-compile:
	pybabel compile -d apollo/translations/
parser:
	canopy apollo/resources/parser/quality.peg --javascript
	mv apollo/resources/parser/quality.js apollo/static/js/
babel-extract:
	pybabel extract -F apollo/babel.cfg -k lazy_gettext -o apollo/translations/messages.pot .
	pybabel extract -F apollo/babel-javascript.cfg -o apollo/translations/javascript.pot .
babel-init:
	pybabel init -i apollo/translations/messages.pot -d apollo/translations/ -l $(LANGUAGE)
	pybabel init -i apollo/translations/javascript.pot -D javascript -d apollo/translations/ -l $(LANGUAGE)
babel-update:
	pybabel update -i apollo/translations/messages.pot -d apollo/translations/
	pybabel update -i apollo/translations/javascript.pot -D javascript -d apollo/translations/
po2json:
	./convert-po2json
