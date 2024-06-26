FROM alpine:3.19@sha256:c5b1261d6d3e43071626931fc004f70149baeba2c8ec672bd4f27761f8e1ad6b

# Non-root user for security purposes.
#
# UIDs below 10,000 are a security risk, as a container breakout could result
# in the container being ran as a more privileged user on the host kernel with
# the same UID.
#
# Static GID/UID is also useful for chown'ing files outside the container where
# such a user does not exist.
RUN addgroup --gid 10001 --system nonroot \
    && adduser  --uid 10000 --system --ingroup nonroot --home /home/nonroot nonroot

# environment settings
ENV PYTHONUNBUFFERED=1

# add local files
COPY root/ /
COPY requirements.txt /app/requirements.txt

WORKDIR /app

RUN \
    echo "**** install packages ****" && \
    apk add --no-cache python3 bash mariadb-client ca-certificates postgresql-client tini && \
    echo "**** install pip ****" && \ 
    python3 -m venv env && \
    /app/env/bin/pip3 install --no-cache --upgrade pip setuptools wheel && \
    /app/env/bin/pip3 install --no-cache -r requirements.txt && \
    echo "**** set up backup location ****" && \
    mkdir /config && \
    mkdir /config/backup && \
    chown -R nonroot:nonroot /config


ENTRYPOINT ["/sbin/tini", "--", "/app/env/bin/python3", "/app/backup.py"]

USER nonroot

CMD ["2>&1", ">", "/config/backup.log"]

