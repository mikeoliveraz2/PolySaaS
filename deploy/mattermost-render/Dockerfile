# PolySaaS Mattermost on Render — Alpine + official team tarball (libc6-compat), not distroless hub image,
# so we can set ListenAddress from PORT and normalize Render Postgres URLs. Pattern follows
# https://github.com/render-examples/mattermost (MIT).
FROM alpine:3.21

ARG MM_VERSION=10.5.1
ARG PUID=2000
ARG PGID=2000

RUN apk add --no-cache \
    bash ca-certificates curl jq libc6-compat tzdata netcat-openbsd \
    && rm -rf /var/cache/apk/*

RUN mkdir -p /mattermost/data /mattermost/plugins /mattermost/client/plugins \
    /var/lib/mattermost/config /var/lib/mattermost/data \
    /var/lib/mattermost/plugins /var/lib/mattermost/client/plugins \
    && curl -fsSL "https://releases.mattermost.com/${MM_VERSION}/mattermost-team-${MM_VERSION}-linux-amd64.tar.gz" \
        | tar -xz \
    && addgroup -g ${PGID} mattermost \
    && adduser -D -u ${PUID} -G mattermost -h /mattermost mattermost \
    && chown -R mattermost:mattermost /mattermost /var/lib/mattermost

COPY entrypoint-render.sh /entrypoint-render.sh
RUN chmod +x /entrypoint-render.sh

USER mattermost
WORKDIR /mattermost
ENV PATH="/mattermost/bin:${PATH}"

EXPOSE 8065

ENTRYPOINT ["/entrypoint-render.sh"]
CMD ["/mattermost/bin/mattermost", "--config", "/var/lib/mattermost/config/config.json"]
