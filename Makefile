.PHONY: pip-compile babel-compile parser babel-extract babel-init babel-update po2json version

audit:
	poetry audit
babel-compile:
	pybabel compile -f -d apollo/translations/
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
deps:
	poetry export --output requirements/prod.txt
	poetry export --with dev --output requirements/dev.txt
po2json:
	./convert-po2json
version:
	./update_version.sh
docker: version
	docker-compose build
