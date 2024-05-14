#!/bin/bash

if [ "${ENV}" = "DEV" ]; then
  pip install --no-cache-dir --require-hashes --no-deps -r /app/requirements/dev.txt
else
  pip install --no-cache-dir --require-hashes --no-deps -r /app/requirements/prod.txt
fi
