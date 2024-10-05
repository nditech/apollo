## PYTHON-BASE
FROM python:3.11-slim AS python-base

LABEL maintainer="Tim Akinbo <takinbo@timbaobjects.com>"

# python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    \
    # pip
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    \
    # poetry
    # https://python-poetry.org/docs/configuration/#using-environment-variables
    POETRY_VERSION=1.8.3 \
    # make poetry install to this location
    POETRY_HOME="/opt/poetry" \
    # make poetry create the virtual environment in the project's root
    # it gets named `.venv`
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    # do not ask any interactive question
    POETRY_NO_INTERACTION=1 \
    \
    # paths
    # this is where our requirements + virtual environment will live
    PYSETUP_PATH="/app" \
    VENV_PATH="/app/.venv"

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        git \
        libgeos-dev \
        libmagic1
RUN git config --global --add safe.directory $PYSETUP_PATH

## BUILDER-BASE
FROM python-base AS builder-base
RUN apt-get install --no-install-recommends -y \
        # deps for installing poetry
        curl \
        # deps for building python deps
        build-essential

# install poetry - respects $POETRY_VERSION & $POETRY_HOME
# The --mount will mount the buildx cache directory to where
# Poetry and Pip store their cache so that they can re-use it
RUN --mount=type=cache,target=/root/.cache \
    curl -sSL https://install.python-poetry.org | python3 -

# copy project requirement files here to ensure they will be cached.
WORKDIR $PYSETUP_PATH

COPY poetry.lock pyproject.toml $PYSETUP_PATH

# install runtime deps - uses $POETRY_VIRTUALENVS_IN_PROJECT internally
RUN --mount=type=cache,target=/root/.cache \
    poetry install --without=dev

COPY . $PYSETUP_PATH
RUN make babel-compile


## DEVELOPMENT

FROM builder-base AS development
ENV FLASK_ENV=development

RUN apt-get install --no-install-recommends -y gpg

# copy in our built poetry + venv
COPY --from=builder-base $POETRY_HOME $POETRY_HOME
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

COPY <<EOF /etc/default/google-chrome
repo_add_once=false
repo_reenable_on_distupgrade=false
EOF

RUN mkdir -p /etc/apt/keyrings
RUN curl --fail --silent --show-error --location https://dl.google.com/linux/linux_signing_key.pub \
        | gpg --dearmor \
        | tee /etc/apt/keyrings/google.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google.gpg] https://dl.google.com/linux/chrome/deb/ stable main" \
        | tee /etc/apt/sources.list.d/google-chrome.list \
    && ln --symbolic /dev/null /etc/apt/trusted.gpg.d/google-chrome.gpg \
    && apt update \
    && apt install --no-install-recommends -y google-chrome-stable

WORKDIR $PYSETUP_PATH

# quicker install as runtime deps are already installed
RUN --mount=type=cache,target=/root/.cache \
    poetry install --with=dev

CMD ["flask", "--app", "apollo.runner", "run", "--reload", "--debug", "--host", "[::]", "--port", "5000"]

EXPOSE 5000


## PRODUCTION

FROM python-base AS production
ENV FLASK_ENV=production
COPY --from=builder-base $POETRY_HOME $POETRY_HOME
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

WORKDIR $PYSETUP_PATH

CMD ["gunicorn", "-c", "gunicorn.conf", "apollo.runner"]

EXPOSE 5000
