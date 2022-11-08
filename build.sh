#!/bin/bash

if [ "${ENV}" = "DEV" ]; then
  pip install --no-cache-dir -r /app/requirements/dev.txt
else
  pip install --no-cache-dir -r /app/requirements/prod.txt
fi