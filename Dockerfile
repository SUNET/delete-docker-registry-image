FROM debian:stable

VOLUME ["/opt/delete-docker-registry-image"]

COPY . /opt/delete-docker-registry-image

RUN /opt/delete-docker-registry-image/docker/setup.sh
WORKDIR /opt/delete-docker-registry-image
