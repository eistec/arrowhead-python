#
# Arrowhead service registry Dockerfile
#
FROM eistec/docker-alpine:latest
MAINTAINER Joakim Nohlgård <joakim.nohlgard@eistec.se>

# Install Python 3 runtime (includes pip3)
# Update pip to the latest release using pip
# Install virtualenv (not needed, since we are in a container?)
# Clean up APK cache
RUN apk add --update \
    python3 \
    shadow \
  && pip3 install --upgrade pip \
  && pip3 install virtualenv \
  && rm -rf /var/cache/apk/*

# Copy files, must run `python setup.py sdist` prior to building in order to create the source package
COPY dist/soa*.tar.gz /tmp/
RUN pip3 install /tmp/soa*.tar.gz && rm /tmp/soa*.tar.gz

# Create application directory and an empty database file
# will run as unprivileged directory user
RUN mkdir -p /opt/core-services \
  && useradd -r -d /opt/core-services -s /sbin/nologin -U directory
COPY sd_server.py /opt/core-services/

# Install startup script
RUN mkdir -p /etc/service/sd_server/
COPY docker/runit/sd_server.sh /etc/service/sd_server/run
