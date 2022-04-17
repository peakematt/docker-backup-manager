FROM alpine:latest

# environment settings
ENV PYTHONUNBUFFERED=1

# add local files
COPY root/ /

RUN \
    echo "**** install packages ****" && \
    apk add --no-cache python3 bash mariadb-client ca-certificates && \
    echo "**** install pip ****" && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \ 
    pip3 install --no-cache --upgrade pip setuptools wheel && \
    pip3 install --no-cache --upgrade boto3 s3cmd && \
    echo "**** configure cron ****" && \
    cat /defaults/backupcron > /etc/crontabs/root


CMD ["crond", "-l2", "-f"]


