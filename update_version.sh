#!/bin/bash
VERSION=`git name-rev --tags --always --name-only $(git rev-parse HEAD)` && sed "s/VERSION=.*/VERSION=$VERSION/" version.ini.tpl > version.ini
COMMIT=`git name-rev --tags --always --name-only --no-undefined $(git rev-parse HEAD)` && sed -i "s/COMMIT=.*/COMMIT=$COMMIT/" version.ini
