FROM alpine/git AS initlayer
WORKDIR /workdir
RUN git clone -b develop https://github.com/PaperMtn/slack-watchman-enterprise-grid.git

FROM python:buster
RUN addgroup --gid 1000 slack-watchman-enterprise-grid
RUN useradd -u 1000 -g 1000 slack-watchman-enterprise-grid
RUN mkdir /home/slack-watchman-enterprise-grid
COPY --from=initlayer /workdir/slack-watchman-enterprise-grid /home/slack-watchman-enterprise-grid
RUN chown -R slack-watchman-enterprise-grid: /home/slack-watchman-enterprise-grid
WORKDIR /home/slack-watchman-enterprise-grid

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install requests build PyYAML numpy
RUN python3 -m build
RUN python3 -m pip install dist/*.whl

USER slack-watchman-enterprise-grid

ENTRYPOINT ["/usr/local/bin/slack-watchman-eg"]