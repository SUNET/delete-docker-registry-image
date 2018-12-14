#!/bin/bash
#
# Install all requirements
#

set -e
set -x

export DEBIAN_FRONTEND noninteractive

# Update the image and install the needed dependencies
# and some common tools for debugging
apt-get update && \
    apt-get -y dist-upgrade && \
    apt-get install -y \
      iputils-ping \
      procps \
      netcat-openbsd \
      python-yaml \
      python-ipaddress \
      python-requests \
    && apt-get -y autoremove \
    && apt-get autoclean

# Do some more cleanup to save space
rm -rf /var/lib/apt/lists/*
