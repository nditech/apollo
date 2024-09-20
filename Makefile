.PHONY: pip-compile babel-compile parser babel-extract babel-init babel-update po2json version

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
po2json:
	./convert-po2json
docker:
	docker-compose build
