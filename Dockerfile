# syntax=docker/dockerfile:1

FROM python:3.10
COPY . /opt/slack-watchman-enterprise-grid
WORKDIR /opt/slack-watchman-enterprise-grid
ENV PYTHONPATH=/opt/slack-watchman-enterprise-grid SLACK_WATCHMAN_EG_TOKEN=""
RUN pip3 install -r requirements.txt build && \
    chmod -R 700 . && \
    python3 -m build && \
    python3 -m pip install dist/*.whl
STOPSIGNAL SIGINT
WORKDIR /opt/slack-watchman-enterprise-grid
ENTRYPOINT ["slack-watchman-eg"]