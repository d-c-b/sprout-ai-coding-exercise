ARG WATCHMAN_VERSION=4.9.0
FROM jotadrilo/watchman:$WATCHMAN_VERSION AS watchman

FROM python:3.10
ENV PYTHONPATH /code
ENV PYTHONUNBUFFERED 1


RUN pip install poetry pywatchman

ARG WATCHMAN_VERSION
COPY --from=watchman /usr/local/bin/watchman* /usr/local/bin/
COPY --from=watchman /usr/local/share/doc/watchman-$WATCHMAN_VERSION /usr/local/share/doc/watchman-$WATCHMAN_VERSION
COPY --from=watchman /usr/local/var/run/watchman /usr/local/var/run/watchman


WORKDIR /code/
COPY pyproject.toml poetry.lock blog_posts.db ./

RUN poetry config virtualenvs.create false
RUN poetry install

COPY ./src /code/src
