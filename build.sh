#!/bin/bash

install_chrome () {
  mkdir /etc/apt/keyrings

  curl --fail --silent --show-error --location https://dl.google.com/linux/linux_signing_key.pub \
    | gpg --dearmor \
    | tee /etc/apt/keyrings/google.gpg

  echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google.gpg] https://dl.google.com/linux/chrome/deb/ stable main" \
    | tee /etc/apt/sources.list.d/google-chrome.list

  # We want to manage the Google Chrome repository manually, so that we can use
  # # the modern `signed-by` method of trusting their key only for their repo, not
  # # globally.
  tee /etc/default/google-chrome <<EOF
repo_add_once=false
repo_reenable_on_distupgrade=false
EOF

  # # They'll auto-install their key globally daily, but we don't want it there.
  ln --symbolic /dev/null /etc/apt/trusted.gpg.d/google-chrome.gpg

  apt update
  apt install -y google-chrome-stable
}

if [ "${ENV}" = "DEV" ]; then
  install_chrome
  pip install --no-cache-dir --require-hashes --no-deps -r /app/requirements/dev.txt
else
  pip install --no-cache-dir --require-hashes --no-deps -r /app/requirements/prod.txt
fi
