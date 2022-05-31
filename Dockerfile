FROM alpine:latest

# environment settings
ENV PYTHONUNBUFFERED=1

# add local files
COPY root/ /

RUN \
    echo "**** install packages ****" && \
    apk add --no-cache python3 bash mariadb-client ca-certificates postgresql-client && \
    echo "**** install pip ****" && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \ 
    pip3 install --no-cache --upgrade pip setuptools wheel && \
    pip3 install --no-cache --upgrade boto3 s3cmd

CMD ["python3", "/app/backup.py", "2>&1", ">", "/config/backup.log"]

